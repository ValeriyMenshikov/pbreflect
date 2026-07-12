"""Tests for PbReflectPlugin."""

import google.protobuf.descriptor_pb2 as descriptor_pb2
from google.protobuf.compiler import plugin_pb2 as plugin

from pbreflect.pbgen.plugins.pbreflect import PbReflectPlugin


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


class TestPbReflectPluginProcessRequest:
    """Tests for PbReflectPlugin.process_request."""

    def test_generates_file_for_proto_with_service(self) -> None:
        proto_file = _make_proto_file_with_service()
        request = plugin.CodeGeneratorRequest()
        request.proto_file.append(proto_file)
        request.file_to_generate.append(proto_file.name)

        plugin_instance = PbReflectPlugin()
        response = plugin_instance.process_request(request)

        assert len(response.file) == 1
        assert response.file[0].name.endswith("_pb2_pbreflect.py")
        assert len(response.file[0].content) > 0

    def test_skips_proto_without_service(self) -> None:
        proto_file = descriptor_pb2.FileDescriptorProto(
            name="no_service.proto",
            package="test.v1",
            syntax="proto3",
        )
        request = plugin.CodeGeneratorRequest()
        request.proto_file.append(proto_file)
        request.file_to_generate.append(proto_file.name)

        plugin_instance = PbReflectPlugin()
        response = plugin_instance.process_request(request)

        assert len(response.file) == 0

    def test_async_param_default_true(self) -> None:
        proto_file = _make_proto_file_with_service()
        request = plugin.CodeGeneratorRequest()
        request.proto_file.append(proto_file)
        request.file_to_generate.append(proto_file.name)
        request.parameter = ""

        plugin_instance = PbReflectPlugin()
        response = plugin_instance.process_request(request)

        assert "async" in response.file[0].content
        assert "grpc.aio" in response.file[0].content

    def test_async_param_false_generates_sync(self) -> None:
        proto_file = _make_proto_file_with_service()
        request = plugin.CodeGeneratorRequest()
        request.proto_file.append(proto_file)
        request.file_to_generate.append(proto_file.name)
        request.parameter = "async=false"

        plugin_instance = PbReflectPlugin()
        response = plugin_instance.process_request(request)

        assert "grpc.aio" not in response.file[0].content

    def test_supported_features_set(self) -> None:
        request = plugin.CodeGeneratorRequest()
        plugin_instance = PbReflectPlugin()
        response = plugin_instance.process_request(request)
        assert response.supported_features == plugin.CodeGeneratorResponse.FEATURE_PROTO3_OPTIONAL
