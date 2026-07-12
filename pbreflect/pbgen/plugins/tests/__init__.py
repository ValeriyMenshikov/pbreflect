"""PbReflect protoc plugin — generates pytest test stubs for gRPC clients."""

import sys
from pathlib import Path

from google.protobuf import descriptor_pb2
from google.protobuf.compiler import plugin_pb2 as plugin

from pbreflect.pbgen.plugins.base import TemplateRenderer, parse_plugin_parameters
from pbreflect.protorecover.reflection_client import GrpcReflectionClient
from pbreflect.utils import name_to_snake


class PbReflectTestsPlugin:
    """Generates per-method pytest test stubs and conftest fixtures."""

    def __init__(self, template_dir: str | None = None) -> None:
        self._descriptor_client = GrpcReflectionClient(channel=None)
        self._renderer = TemplateRenderer(
            default_dir=Path(__file__).parent / "templates",
            custom_dir=template_dir,
            extra_filters={"to_snake": name_to_snake},
        )

    @staticmethod
    def _pb2_module(proto_file: descriptor_pb2.FileDescriptorProto) -> str:
        return proto_file.name.replace(".proto", "_pb2").replace("/", ".").replace("-", "_")

    @staticmethod
    def _pb2_pbreflect_module(proto_file: descriptor_pb2.FileDescriptorProto) -> str:
        return proto_file.name.replace(".proto", "_pb2_pbreflect").replace("/", ".").replace("-", "_")

    @staticmethod
    def _method_imports(method: dict) -> tuple[str | None, str | None]:
        if method["is_client_streaming"]:
            return None, None
        input_type: str = method["input_type"]
        if "." in input_type:
            module_part = input_type.split(".")[0]
            if module_part.endswith("_pb2"):
                return None, f"from google.protobuf import {module_part}"
            return None, None
        return input_type, None

    def generate_method_file(
        self,
        proto_file: descriptor_pb2.FileDescriptorProto,
        service: dict,
        method: dict,
        *,
        client_module: str,
        async_mode: bool,
    ) -> str:
        local_type, extra_import = self._method_imports(method)
        return self._renderer.render(
            "test_method.jinja2",
            service=service,
            method=method,
            client_module=client_module,
            pb2_module=self._pb2_module(proto_file),
            pb2_pbreflect_module=self._pb2_pbreflect_module(proto_file),
            local_type=local_type,
            extra_import=extra_import,
            async_mode=async_mode,
        )

    def generate_root_conftest(self, *, async_mode: bool) -> str:
        return self._renderer.render("conftest.jinja2", async_mode=async_mode)

    def generate_service_conftest(
        self,
        proto_file: descriptor_pb2.FileDescriptorProto,
        service: dict,
        *,
        client_module: str,
        async_mode: bool,
    ) -> str:
        return self._renderer.render(
            "conftest_service.jinja2",
            service=service,
            client_module=client_module,
            pb2_pbreflect_module=self._pb2_pbreflect_module(proto_file),
            async_mode=async_mode,
        )

    def process_request(self, request: plugin.CodeGeneratorRequest) -> plugin.CodeGeneratorResponse:
        response = plugin.CodeGeneratorResponse()
        response.supported_features = plugin.CodeGeneratorResponse.FEATURE_PROTO3_OPTIONAL

        params = parse_plugin_parameters(request.parameter)
        client_module: str = params.get("client_module", "clients")
        async_mode: bool = params.get("async", "false").lower() == "true"

        has_services = False

        for proto_file in request.proto_file:
            if not proto_file.service:
                continue

            for service in self._descriptor_client.get_services(proto_file):
                has_services = True
                pkg = name_to_snake(service["name"])

                init_file = response.file.add()
                init_file.name = f"{pkg}/__init__.py"
                init_file.content = ""

                svc_conftest = response.file.add()
                svc_conftest.name = f"{pkg}/conftest.py"
                svc_conftest.content = self.generate_service_conftest(
                    proto_file, service, client_module=client_module, async_mode=async_mode
                )

                for method in service["methods"]:
                    test_file = response.file.add()
                    test_file.name = f"{pkg}/test_{method['name']}.py"
                    test_file.content = self.generate_method_file(
                        proto_file, service, method, client_module=client_module, async_mode=async_mode
                    )

        if has_services:
            root_conftest = response.file.add()
            root_conftest.name = "conftest.py"
            root_conftest.content = self.generate_root_conftest(async_mode=async_mode)

        return response


def main() -> None:
    """Entry point for the protoc-gen-pbreflect_tests plugin."""
    data = sys.stdin.buffer.read()
    request = plugin.CodeGeneratorRequest()
    request.ParseFromString(data)

    params = parse_plugin_parameters(request.parameter)
    plugin_instance = PbReflectTestsPlugin(template_dir=params.get("t"))
    response = plugin_instance.process_request(request)
    sys.stdout.buffer.write(response.SerializeToString())


if __name__ == "__main__":
    main()
