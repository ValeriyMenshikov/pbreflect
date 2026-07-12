import re
from pathlib import Path
from typing import Any, final

import google.protobuf.descriptor_pb2 as descriptor_pb2
from jinja2 import Environment, FileSystemLoader


@final
class ProtoFileBuilder:
    """Builder for generating .proto files from FileDescriptorProto objects.

    This class takes a FileDescriptorProto object and generates the corresponding
    .proto file content using Jinja2 templates.
    """

    def __init__(self) -> None:
        """Initialize the ProtoFileBuilder."""
        self.env = Environment(  # noqa: S701
            loader=FileSystemLoader(str(Path(__file__).parent / "templates")),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def get_proto(self, descriptor: descriptor_pb2.FileDescriptorProto) -> tuple[str, str]:
        """Generate a .proto file from a FileDescriptorProto.

        Args:
            descriptor: The FileDescriptorProto object containing the proto definition

        Returns:
            A tuple containing (file_name, file_content)
        """
        syntax = descriptor.syntax or "proto2"
        package = descriptor.package
        imports: list[tuple[list[str], str]] = []

        for index, dep in enumerate(descriptor.dependency):
            prefix = []
            if index in descriptor.public_dependency:
                prefix.append("public")
            if index in descriptor.weak_dependency:
                prefix.append("weak")
            imports.append((prefix, self._normalize_dependency_import(dep)))

        content = self._parse_msgs_and_services(descriptor, [""], syntax, package)

        template = self.env.get_template("file.proto.j2")
        rendered = template.render(syntax=syntax, package=package, imports=imports, content=content.strip())

        name = descriptor.name.replace("..", "").strip("./\\")
        return name, rendered

    @staticmethod
    def _normalize_dependency_import(dep: str) -> str:
        """Normalize dependency import paths coming from reflection.

        Some servers may expose malformed dependency paths that accidentally
        concatenate a repository prefix with an absolute import path, e.g.:
            foo/bar/service-example/gitlab.example.com/x/y.proto

        Protobuf import resolution expects the canonical import path.
        We apply a conservative heuristic: if the dependency contains multiple
        domain-like prefixes (host.tld/), keep the substring starting from the
        last such prefix.
        """
        # Match domain-like segments followed by a slash (e.g. gitlab.example.ru/).
        matches = list(re.finditer(r"[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+/", dep))
        if len(matches) <= 1:
            return dep

        return dep[matches[-1].start() :]

    def _parse_msgs_and_services(
        self, desc: descriptor_pb2.FileDescriptorProto, scopes: list[str], syntax: str, package: str
    ) -> str:
        out = ""
        for service in getattr(desc, "service", []):
            out += self._render_service(service, package)
        for nested_msg in getattr(desc, "nested_type", []):
            out += self._render_message(nested_msg, scopes, syntax, package)
        for message in getattr(desc, "message_type", []):
            out += self._render_message(message, scopes, syntax, package)
        for enum in desc.enum_type:
            out += self._render_enum(enum)
        return out

    def _render_enum(self, enum: descriptor_pb2.EnumDescriptorProto) -> str:
        """Render an enum definition.

        Args:
            enum: The EnumDescriptorProto to render

        Returns:
            String containing the rendered enum definition
        """
        values = [(val.name, val.number) for val in enum.value]
        template = self.env.get_template("enum.proto.j2")
        return template.render(name=enum.name, options=[], values=values)

    def _render_service(self, service: descriptor_pb2.ServiceDescriptorProto, package: str) -> str:
        methods: list[dict[str, Any]] = [
            {
                "name": m.name,
                "input_type": self._format_type(m.input_type, package),
                "output_type": self._format_type(m.output_type, package),
                "client_streaming": m.client_streaming,
                "server_streaming": m.server_streaming,
            }
            for m in service.method
        ]
        return self.env.get_template("service.proto.j2").render(name=service.name, methods=methods)

    @staticmethod
    def _format_type(type_name: str, package: str) -> str:
        type_path = type_name.strip(".")
        if package and type_path.startswith(package):
            return type_path[len(package) + 1 :]
        return type_path

    def _render_message(
        self, message: descriptor_pb2.DescriptorProto, scopes: list[str], syntax: str, package: str
    ) -> str:
        if message.options.map_entry:
            return ""

        map_entries = {nested.name: nested for nested in message.nested_type if nested.options.map_entry}
        fields: list[dict[str, Any]] = []
        oneofs: dict[str, list[dict[str, Any]]] = {}

        for f in message.field:
            if (
                f.type == descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE
                and f.type_name.split(".")[-1] in map_entries
            ):
                entry = map_entries[f.type_name.split(".")[-1]]
                key_field = next(kf for kf in entry.field if kf.name == "key")
                value_field = next(vf for vf in entry.field if vf.name == "value")
                field_info = {
                    "label": "",
                    "type": (
                        f"map<{self._resolve_type(key_field, package)}, "
                        f"{self._resolve_type(value_field, package)}>"
                    ),
                    "name": f.name,
                    "number": f.number,
                }
            else:
                field_info = {
                    "label": "" if f.HasField("oneof_index") else self._labels[f.label],
                    "type": self._resolve_type(f, package),
                    "name": f.name,
                    "number": f.number,
                }

            if f.HasField("oneof_index"):
                oneofs.setdefault(message.oneof_decl[f.oneof_index].name, []).append(field_info)
            else:
                fields.append(field_info)

        enums = [self._render_enum(e) for e in message.enum_type]
        nested_msgs = [
            self._render_message(n, scopes, syntax, package)
            for n in message.nested_type
            if not n.options.map_entry
        ]

        return self.env.get_template("message.proto.j2").render(
            name=message.name,
            fields=fields,
            oneofs=oneofs,
            nested_msgs=nested_msgs,
            enums=enums,
            options=[],
        )

    def _resolve_type(self, field: descriptor_pb2.FieldDescriptorProto, package: str) -> str:
        if field.type_name:
            type_path = field.type_name.strip(".")
            if package and type_path.startswith(package):
                return type_path[len(package) + 1 :]
            return type_path
        return self._types[field.type]

    @property
    def _types(self) -> dict[int, str]:
        """Map of field type enum values to their string representations."""
        return {v: k.split("_")[1].lower() for k, v in descriptor_pb2.FieldDescriptorProto.Type.items()}

    @property
    def _labels(self) -> dict[int, str]:
        """Map of field label enum values to their string representations."""
        return {v: k.split("_")[1].lower() for k, v in descriptor_pb2.FieldDescriptorProto.Label.items()}
