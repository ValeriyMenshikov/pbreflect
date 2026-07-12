"""PbReflect protoc plugin — generates typed gRPC client wrappers."""

import sys
from pathlib import Path

from google.protobuf import descriptor_pb2
from google.protobuf.compiler import plugin_pb2 as plugin

from pbreflect.pbgen.plugins.base import TemplateRenderer, parse_plugin_parameters
from pbreflect.protorecover.reflection_client import GrpcReflectionClient


class PbReflectPlugin:
    """Generates PbReflect client code from proto descriptors."""

    def __init__(self, template_dir: str | None = None) -> None:
        self._descriptor_client = GrpcReflectionClient(channel=None)
        self._renderer = TemplateRenderer(
            default_dir=Path(__file__).parent / "templates",
            custom_dir=template_dir,
        )

    def generate_code(self, proto_file: descriptor_pb2.FileDescriptorProto, async_mode: bool = True) -> str:
        return self._renderer.render(
            "client.jinja2",
            package=proto_file.package,
            imports=self._descriptor_client.get_imports(proto_file),
            services=self._descriptor_client.get_services(proto_file),
            messages=self._descriptor_client.get_messages(proto_file),
            enums=self._descriptor_client.get_enums(proto_file),
            async_mode=async_mode,
        )

    def process_request(self, request: plugin.CodeGeneratorRequest) -> plugin.CodeGeneratorResponse:
        response = plugin.CodeGeneratorResponse()
        response.supported_features = plugin.CodeGeneratorResponse.FEATURE_PROTO3_OPTIONAL

        params = parse_plugin_parameters(request.parameter)
        async_mode = params.get("async", "true").lower() == "true"

        for proto_file in request.proto_file:
            if not proto_file.service:
                continue
            output_file = response.file.add()
            output_file.name = self._descriptor_client.get_output_filename(proto_file)
            output_file.content = self.generate_code(proto_file, async_mode=async_mode)

        return response


def main() -> None:
    """Entry point for the protoc-gen-pbreflect plugin."""
    data = sys.stdin.buffer.read()
    request = plugin.CodeGeneratorRequest()
    request.ParseFromString(data)

    params = parse_plugin_parameters(request.parameter)
    plugin_instance = PbReflectPlugin(template_dir=params.get("t"))
    response = plugin_instance.process_request(request)
    sys.stdout.buffer.write(response.SerializeToString())


if __name__ == "__main__":
    main()
