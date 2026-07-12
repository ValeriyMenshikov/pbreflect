"""Tests for PbReflectTestsPlugin."""

import google.protobuf.descriptor_pb2 as descriptor_pb2
from google.protobuf.compiler import plugin_pb2 as plugin

from pbreflect.pbgen.plugins.tests import PbReflectTestsPlugin


def _make_proto_file_with_service(
    name: str = "test.proto",
    package: str = "test.v1",
    service_name: str = "UserService",
) -> descriptor_pb2.FileDescriptorProto:
    proto_file = descriptor_pb2.FileDescriptorProto(name=name, package=package, syntax="proto3")
    svc = proto_file.service.add()
    svc.name = service_name
    method = svc.method.add()
    method.name = "GetUser"
    method.input_type = f".{package}.GetUserRequest"
    method.output_type = f".{package}.GetUserResponse"
    return proto_file


class TestPbReflectTestsPluginProcessRequest:
    """Tests for PbReflectTestsPlugin.process_request."""

    def test_generates_test_files_for_service(self) -> None:
        proto_file = _make_proto_file_with_service()
        request = plugin.CodeGeneratorRequest()
        request.proto_file.append(proto_file)
        request.file_to_generate.append(proto_file.name)
        request.parameter = "client_module=clients"

        plugin_instance = PbReflectTestsPlugin()
        response = plugin_instance.process_request(request)

        file_names = [f.name for f in response.file]
        assert any("conftest.py" in name for name in file_names)
        assert any("test_get_user.py" in name for name in file_names)
        assert any("__init__.py" in name for name in file_names)

    def test_skips_proto_without_service(self) -> None:
        proto_file = descriptor_pb2.FileDescriptorProto(
            name="no_service.proto",
            package="test.v1",
        )
        request = plugin.CodeGeneratorRequest()
        request.proto_file.append(proto_file)
        request.file_to_generate.append(proto_file.name)

        plugin_instance = PbReflectTestsPlugin()
        response = plugin_instance.process_request(request)

        assert len(response.file) == 0

    def test_generates_root_conftest_when_services_exist(self) -> None:
        proto_file = _make_proto_file_with_service()
        request = plugin.CodeGeneratorRequest()
        request.proto_file.append(proto_file)
        request.file_to_generate.append(proto_file.name)

        plugin_instance = PbReflectTestsPlugin()
        response = plugin_instance.process_request(request)

        conftest_files = [f for f in response.file if f.name == "conftest.py"]
        assert len(conftest_files) == 1
        assert "grpc_channel" in conftest_files[0].content

    def test_no_root_conftest_when_no_services(self) -> None:
        proto_file = descriptor_pb2.FileDescriptorProto(
            name="no_service.proto",
            package="test.v1",
        )
        request = plugin.CodeGeneratorRequest()
        request.proto_file.append(proto_file)
        request.file_to_generate.append(proto_file.name)

        plugin_instance = PbReflectTestsPlugin()
        response = plugin_instance.process_request(request)

        conftest_files = [f for f in response.file if f.name == "conftest.py"]
        assert len(conftest_files) == 0
