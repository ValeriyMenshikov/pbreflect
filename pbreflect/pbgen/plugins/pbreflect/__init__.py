"""PbReflect plugin for protoc."""

import sys
from pathlib import Path
from typing import Any

import jinja2
from google.protobuf import descriptor_pb2
from google.protobuf.compiler import plugin_pb2 as plugin

from pbreflect.protorecover.reflection_client import GrpcReflectionClient


class PbReflectPlugin:
    """Plugin for generating PbReflect client code."""

    def __init__(self) -> None:
        """Initialize the plugin."""
        # Create client for working with descriptors
        # For the plugin, we don't need a real channel as we work with descriptors directly
        self.descriptor_client = GrpcReflectionClient(channel=None)

    @staticmethod
    def get_template_path() -> Path:
        """Get path to templates directory.

        Returns:
            Path to templates directory
        """
        # Determine the path to the templates directory
        current_dir = Path(__file__).parent
        template_dir = current_dir / "templates"
        return template_dir

    def get_template(self, template_name: str) -> jinja2.Template:
        """Get Jinja2 template by name.

        Args:
            template_name: Name of the template

        Returns:
            Jinja2 template
        """
        # Create Jinja2 environment
        template_path = self.get_template_path()
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_path),
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=True,
        )
        return env.get_template(template_name)

    def generate_code(self, proto_file: descriptor_pb2.FileDescriptorProto, async_mode: bool = True) -> str:
        """Generate code for the given proto file.

        Args:
            proto_file: Proto file descriptor
            async_mode: Whether to generate async client code (True) or sync client code (False)

        Returns:
            Generated code
        """
        template = self.get_template("client.jinja2")

        context = {
            "package": proto_file.package,
            "imports": self.descriptor_client.get_imports(proto_file),
            "services": self.descriptor_client.get_services(proto_file),
            "messages": self.descriptor_client.get_messages(proto_file),
            "enums": self.descriptor_client.get_enums(proto_file),
            "async_mode": async_mode,
        }

        rendered = template.render(**context)

        return rendered

    def parse_parameters(self, parameter_string: str) -> dict[str, Any]:
        """Parse plugin parameters.

        Args:
            parameter_string: Parameter string from protoc

        Returns:
            Dictionary of parsed parameters
        """
        parameters: dict[str, Any] = {}
        if not parameter_string:
            return parameters

        for param in parameter_string.split(","):
            if "=" in param:
                key, value = param.split("=", 1)
                parameters[key.strip()] = value.strip()
            else:
                parameters[param.strip()] = True

        return parameters

    def process_request(self, request: plugin.CodeGeneratorRequest) -> plugin.CodeGeneratorResponse:
        """Process the code generator request.

        Args:
            request: Code generator request

        Returns:
            Code generator response
        """
        # Create response
        response = plugin.CodeGeneratorResponse()

        # Indicate that we support optional fields in proto3
        response.supported_features = plugin.CodeGeneratorResponse.FEATURE_PROTO3_OPTIONAL

        # Parse parameters
        parameters = self.parse_parameters(request.parameter)
        async_mode = parameters.get("async", "true").lower() == "true"

        # Process each file
        for proto_file in request.proto_file:
            # Skip files without services
            if not proto_file.service:
                continue

            # Generate code
            code = self.generate_code(proto_file, async_mode=async_mode)

            # Create output file
            output_file = response.file.add()
            output_file.name = self.descriptor_client.get_output_filename(proto_file)
            output_file.content = code

        return response


def main() -> None:
    """Main entry point for the plugin."""
    # Read request from stdin
    data = sys.stdin.buffer.read()

    # Parse request
    request = plugin.CodeGeneratorRequest()
    request.ParseFromString(data)

    # Process request
    plugin_instance = PbReflectPlugin()
    response = plugin_instance.process_request(request)

    # Write response to stdout
    sys.stdout.buffer.write(response.SerializeToString())


if __name__ == "__main__":
    main()
