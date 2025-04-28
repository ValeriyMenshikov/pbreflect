import re
from pathlib import Path
from collections import OrderedDict
from itertools import groupby

from jinja2 import Environment, FileSystemLoader
import google.protobuf.descriptor_pb2 as descriptor_pb2


class ProtoRecover:
    def __init__(
        self, descriptor: descriptor_pb2.FileDescriptorProto, templates_dir: Path = None
    ):
        self.descriptor = descriptor
        self.env = Environment(
            loader=FileSystemLoader(
                str(templates_dir or Path(__file__).parent / "templates")
            ),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def get_proto(self, output_dir: Path = None):
        syntax = self.descriptor.syntax or "proto2"
        package = self.descriptor.package
        imports = []
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
        proto = {"name": name, "content": rendered}
        file_path = self._write_proto_file(proto, output_dir=output_dir)

        return file_path

    @staticmethod
    def _write_proto_file(proto: dict, output_dir: Path = None):
        parts = proto["name"].rsplit(".", 1)
        directory = parts[0].replace(".", "/")
        new_path = directory if len(parts) == 1 else f"{directory}.{parts[1]}"
        proto_name = output_dir / new_path
        proto_name.parent.mkdir(parents=True, exist_ok=True)
        with open(proto_name, "w") as f:
            f.write(proto["content"])
        return proto_name

    def _parse_msgs_and_services(self, desc, scopes, syntax):
        out = ""

        for enum in desc.enum_type:
            out += self._render_enum(enum)

        for nested_msg in getattr(desc, "nested_type", []):
            out += self._render_message(nested_msg, scopes, syntax)

        for service in getattr(desc, "service", []):
            out += self._render_service(service)

        for message in getattr(desc, "message_type", []):
            out += self._render_message(message, scopes, syntax)

        return out

    def _render_enum(self, enum):
        values = [(val.name, val.number) for val in enum.value]
        template = self.env.get_template("enum.proto.j2")
        return template.render(name=enum.name, options=[], values=values)

    def _render_service(self, service):
        methods = []
        for method in service.method:
            methods.append(
                {
                    "name": method.name,
                    "input_type": method.input_type.split(".")[-1],
                    "output_type": method.output_type.split(".")[-1],
                    "client_streaming": method.client_streaming,
                    "server_streaming": method.server_streaming,
                }
            )
        template = self.env.get_template("service.proto.j2")
        return template.render(name=service.name, methods=methods)

    def _render_message(self, message, scopes, syntax):
        fields = []
        oneofs = {}
        nested_msgs = []
        enums = []

        if message.options.map_entry:
            return ""

        for field in message.field:
            field_info = {
                "label": self._labels[field.label],
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

    def _resolve_type(self, field):
        if field.type_name:
            return field.type_name.split(".")[-1]
        return self._types[field.type]

    @property
    def _types(self):
        return {
            v: k.split("_")[1].lower()
            for k, v in descriptor_pb2.FieldDescriptorProto.Type.items()
        }

    @property
    def _labels(self):
        return {
            v: k.split("_")[1].lower()
            for k, v in descriptor_pb2.FieldDescriptorProto.Label.items()
        }
