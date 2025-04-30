from pathlib import Path
from typing import Optional, Any, Union

from jinja2 import Environment, FileSystemLoader
import google.protobuf.descriptor_pb2 as descriptor_pb2


class ProtoFileBuilder:
    def __init__(self) -> None:
        self.descriptor: Optional[descriptor_pb2.FileDescriptorProto] = None
        self.env = Environment(
            loader=FileSystemLoader(str(Path(__file__).parent / "templates")),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def get_proto(self, descriptor: descriptor_pb2.FileDescriptorProto) -> tuple[str, str]:
        self.descriptor = descriptor
        syntax = self.descriptor.syntax or "proto2"
        package = self.descriptor.package
        imports: list[tuple[list[str], str]] = []
        for index, dep in enumerate(self.descriptor.dependency):
            prefix = []
            if index in self.descriptor.public_dependency:
                prefix.append("public")
            if index in self.descriptor.weak_dependency:
                prefix.append("weak")
            imports.append((prefix, dep))

        content = self._parse_msgs_and_services(self.descriptor, [""], syntax)

        template = self.env.get_template("file.proto.j2")
        rendered = template.render(
            syntax=syntax, package=package, imports=imports, content=content.strip()
        )

        name = self.descriptor.name.replace("..", "").strip(".\/")

        return name, rendered

    def _parse_msgs_and_services(self, desc: descriptor_pb2.FileDescriptorProto, scopes: list[str], syntax: str) -> str:
        out = ""

        for service in getattr(desc, "service", []):
            out += self._render_service(service)

        for nested_msg in getattr(desc, "nested_type", []):
            out += self._render_message(nested_msg, scopes, syntax)

        for message in getattr(desc, "message_type", []):
            out += self._render_message(message, scopes, syntax)

        for enum in desc.enum_type:
            out += self._render_enum(enum)

        return out

    def _render_enum(self, enum: descriptor_pb2.EnumDescriptorProto) -> str:
        values = [(val.name, val.number) for val in enum.value]
        template = self.env.get_template("enum.proto.j2")
        return template.render(name=enum.name, options=[], values=values)

    def _render_service(self, service: descriptor_pb2.ServiceDescriptorProto) -> str:
        methods: list[dict[str, Any]] = []
        for method in service.method:
            methods.append(
                {
                    "name": method.name,
                    "input_type": self._format_type(method.input_type),
                    "output_type": self._format_type(method.output_type),
                    "client_streaming": method.client_streaming,
                    "server_streaming": method.server_streaming,
                }
            )
        template = self.env.get_template("service.proto.j2")
        return template.render(name=service.name, methods=methods)

    def _format_type(self, type_name: str) -> str:
        type_path = type_name.strip(".")
        if self.descriptor and self.descriptor.package and type_path.startswith(self.descriptor.package):
            return type_path[len(self.descriptor.package) + 1 :]
        return type_path

    def _render_message(self, message: descriptor_pb2.DescriptorProto, scopes: list[str], syntax: str) -> str:
        fields: list[dict[str, Any]] = []
        oneofs: dict[str, list[dict[str, Any]]] = {}
        nested_msgs: list[str] = []
        enums: list[str] = []

        if message.options.map_entry:
            return ""

        map_entries = {
            nested.name: nested
            for nested in message.nested_type
            if nested.options.map_entry
        }

        for field in message.field:
            if (
                field.type == descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE
                and field.type_name.split(".")[-1] in map_entries
            ):
                entry = map_entries[field.type_name.split(".")[-1]]
                key_field = next(f for f in entry.field if f.name == "key")
                value_field = next(f for f in entry.field if f.name == "value")

                field_info = {
                    "label": "",
                    "type": f"map<{self._resolve_type(key_field)}, {self._resolve_type(value_field)}>",
                    "name": field.name,
                    "number": field.number,
                }
            else:
                field_info = {
                    "label": ""
                    if field.HasField("oneof_index")
                    else self._labels[field.label],
                    "type": self._resolve_type(field),
                    "name": field.name,
                    "number": field.number,
                }

            if field.HasField("oneof_index"):
                oneofs.setdefault(
                    message.oneof_decl[field.oneof_index].name, []
                ).append(field_info)
            else:
                fields.append(field_info)

        for nested_enum in message.enum_type:
            enums.append(self._render_enum(nested_enum))

        for nested in message.nested_type:
            if not nested.options.map_entry:
                nested_msgs.append(self._render_message(nested, scopes, syntax))

        template = self.env.get_template("message.proto.j2")
        return template.render(
            name=message.name,
            fields=fields,
            oneofs=oneofs,
            nested_msgs=nested_msgs,
            enums=enums,
            options=[],
        )

    def _resolve_type(self, field: descriptor_pb2.FieldDescriptorProto) -> str:
        if field.type_name:
            type_path = field.type_name.strip(".")
            if self.descriptor and self.descriptor.package and type_path.startswith(
                self.descriptor.package
            ):
                return type_path[len(self.descriptor.package) + 1 :]
            else:
                return type_path
        return self._types[field.type]

    @property
    def _types(self) -> dict[int, str]:
        return {
            v: k.split("_")[1].lower()
            for k, v in descriptor_pb2.FieldDescriptorProto.Type.items()
        }

    @property
    def _labels(self) -> dict[int, str]:
        return {
            v: k.split("_")[1].lower()
            for k, v in descriptor_pb2.FieldDescriptorProto.Label.items()
        }