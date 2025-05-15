from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, final, ClassVar

from jinja2 import Environment, FileSystemLoader
import google.protobuf.descriptor_pb2 as descriptor_pb2


@final
class ProtoFileBuilder:
    """Builder for generating .proto files from FileDescriptorProto objects.

    This class takes a FileDescriptorProto object and generates the corresponding
    .proto file content using Jinja2 templates.
    """

    def __init__(self) -> None:
        """Initialize the ProtoFileBuilder."""
        self.descriptor: Optional[descriptor_pb2.FileDescriptorProto] = None
        self.env = Environment(
            loader=FileSystemLoader(str(Path(__file__).parent / "templates")),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def get_proto(self, descriptor: descriptor_pb2.FileDescriptorProto) -> Tuple[str, str]:
        """Generate a .proto file from a FileDescriptorProto.

        Args:
            descriptor: The FileDescriptorProto object containing the proto definition

        Returns:
            A tuple containing (file_name, file_content)
        """
        self.descriptor = descriptor
        syntax = self.descriptor.syntax or "proto2"
        package = self.descriptor.package
        imports: List[Tuple[List[str], str]] = []

        # Process imports and their qualifiers (public/weak)
        for index, dep in enumerate(self.descriptor.dependency):
            prefix = []
            if index in self.descriptor.public_dependency:
                prefix.append("public")
            if index in self.descriptor.weak_dependency:
                prefix.append("weak")
            imports.append((prefix, dep))

        # Generate the content for messages, enums, and services
        content = self._parse_msgs_and_services(self.descriptor, [""], syntax)

        # Render the complete proto file using the template
        template = self.env.get_template("file.proto.j2")
        rendered = template.render(
            syntax=syntax, package=package, imports=imports, content=content.strip()
        )

        # Normalize the file name
        name = self.descriptor.name.replace("..", "").strip(".\/")

        return name, rendered

    def _parse_msgs_and_services(
        self, desc: descriptor_pb2.FileDescriptorProto, scopes: List[str], syntax: str
    ) -> str:
        """Parse messages, services, and enums from a FileDescriptorProto.

        Args:
            desc: The FileDescriptorProto to parse
            scopes: List of scope names for nested messages
            syntax: Proto syntax version (proto2 or proto3)

        Returns:
            String containing the rendered proto content
        """
        out = ""

        # Process services
        for service in getattr(desc, "service", []):
            out += self._render_service(service)

        # Process nested types
        for nested_msg in getattr(desc, "nested_type", []):
            out += self._render_message(nested_msg, scopes, syntax)

        # Process top-level messages
        for message in getattr(desc, "message_type", []):
            out += self._render_message(message, scopes, syntax)

        # Process enums
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

    def _render_service(self, service: descriptor_pb2.ServiceDescriptorProto) -> str:
        """Render a service definition.

        Args:
            service: The ServiceDescriptorProto to render

        Returns:
            String containing the rendered service definition
        """
        methods: List[Dict[str, Any]] = []
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
        """Format a type name by removing package prefix if it's in the same package.

        Args:
            type_name: The fully-qualified type name

        Returns:
            Formatted type name
        """
        type_path = type_name.strip(".")
        if (
            self.descriptor
            and self.descriptor.package
            and type_path.startswith(self.descriptor.package)
        ):
            return type_path[len(self.descriptor.package) + 1 :]
        return type_path

    def _render_message(
        self, message: descriptor_pb2.DescriptorProto, scopes: List[str], syntax: str
    ) -> str:
        """Render a message definition.

        Args:
            message: The DescriptorProto to render
            scopes: List of scope names for nested messages
            syntax: Proto syntax version (proto2 or proto3)

        Returns:
            String containing the rendered message definition
        """
        fields: List[Dict[str, Any]] = []
        oneofs: Dict[str, List[Dict[str, Any]]] = {}
        nested_msgs: List[str] = []
        enums: List[str] = []

        # Skip map entry messages as they're handled specially
        if message.options.map_entry:
            return ""

        # Identify map entry messages for special handling
        map_entries = {
            nested.name: nested for nested in message.nested_type if nested.options.map_entry
        }

        # Process each field
        for field in message.field:
            # Special handling for map fields
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
                    "label": "" if field.HasField("oneof_index") else self._labels[field.label],
                    "type": self._resolve_type(field),
                    "name": field.name,
                    "number": field.number,
                }

            # Handle oneof fields
            if field.HasField("oneof_index"):
                oneof_name = message.oneof_decl[field.oneof_index].name
                oneofs.setdefault(oneof_name, []).append(field_info)
            else:
                fields.append(field_info)

        # Process nested enums
        for nested_enum in message.enum_type:
            enums.append(self._render_enum(nested_enum))

        # Process nested messages (excluding map entries)
        for nested in message.nested_type:
            if not nested.options.map_entry:
                nested_msgs.append(self._render_message(nested, scopes, syntax))

        # Render the message using the template
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
        """Resolve the type name for a field.

        Args:
            field: The FieldDescriptorProto to resolve the type for

        Returns:
            The resolved type name
        """
        if field.type_name:
            # It's a named type (message or enum)
            type_path = field.type_name.strip(".")
            if (
                self.descriptor
                and self.descriptor.package
                and type_path.startswith(self.descriptor.package)
            ):
                # Remove package prefix for types in the same package
                return type_path[len(self.descriptor.package) + 1 :]
            else:
                return type_path
        # It's a primitive type
        return self._types[field.type]

    @property
    def _types(self) -> Dict[int, str]:
        """Map of field type enum values to their string representations."""
        return {
            v: k.split("_")[1].lower() for k, v in descriptor_pb2.FieldDescriptorProto.Type.items()
        }

    @property
    def _labels(self) -> Dict[int, str]:
        """Map of field label enum values to their string representations."""
        return {
            v: k.split("_")[1].lower() for k, v in descriptor_pb2.FieldDescriptorProto.Label.items()
        }
