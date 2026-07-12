"""Tests for GrpcReflectionClient public methods."""

import google.protobuf.descriptor_pb2 as descriptor_pb2
import pytest

from pbreflect.protorecover.reflection_client import GrpcReflectionClient


@pytest.fixture
def client() -> GrpcReflectionClient:
    return GrpcReflectionClient(channel=None)


def _make_proto_file(
    name: str = "test.proto",
    package: str = "test.v1",
) -> descriptor_pb2.FileDescriptorProto:
    return descriptor_pb2.FileDescriptorProto(name=name, package=package)


class TestGetServiceMethods:
    """Tests for get_service_methods."""

    def test_returns_methods_with_snake_names(self, client: GrpcReflectionClient) -> None:
        service = descriptor_pb2.ServiceDescriptorProto()
        method = service.method.add()
        method.name = "GetUser"
        method.input_type = ".test.v1.GetUserRequest"
        method.output_type = ".test.v1.GetUserResponse"

        result = client.get_service_methods(service)
        assert len(result) == 1
        assert result[0]["name"] == "get_user"
        assert result[0]["original_name"] == "GetUser"
        assert result[0]["input_type"] == "GetUserRequest"
        assert result[0]["output_type"] == "GetUserResponse"
        assert result[0]["is_server_streaming"] is False
        assert result[0]["is_client_streaming"] is False

    def test_strips_leading_dot_from_types(self, client: GrpcReflectionClient) -> None:
        service = descriptor_pb2.ServiceDescriptorProto()
        method = service.method.add()
        method.name = "DoThing"
        method.input_type = ".my.pkg.ThingRequest"
        method.output_type = ".my.pkg.ThingResponse"

        result = client.get_service_methods(service)
        assert result[0]["input_type"] == "ThingRequest"
        assert result[0]["output_type"] == "ThingResponse"

    def test_google_protobuf_type_conversion(self, client: GrpcReflectionClient) -> None:
        service = descriptor_pb2.ServiceDescriptorProto()
        method = service.method.add()
        method.name = "Ping"
        method.input_type = ".google.protobuf.Empty"
        method.output_type = ".google.protobuf.Empty"

        result = client.get_service_methods(service)
        assert result[0]["input_type"] == "empty_pb2.Empty"
        assert result[0]["output_type"] == "empty_pb2.Empty"

    def test_streaming_flags(self, client: GrpcReflectionClient) -> None:
        service = descriptor_pb2.ServiceDescriptorProto()
        method = service.method.add()
        method.name = "StreamData"
        method.input_type = ".test.Request"
        method.output_type = ".test.Response"
        method.client_streaming = True
        method.server_streaming = True

        result = client.get_service_methods(service)
        assert result[0]["is_client_streaming"] is True
        assert result[0]["is_server_streaming"] is True


class TestGetMessageFields:
    """Tests for get_message_fields."""

    def test_returns_field_info(self, client: GrpcReflectionClient) -> None:
        msg = descriptor_pb2.DescriptorProto(name="User")
        field = msg.field.add()
        field.name = "id"
        field.number = 1
        field.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING
        field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL

        result = client.get_message_fields(msg)
        assert len(result) == 1
        assert result[0]["name"] == "id"
        assert result[0]["number"] == 1
        assert result[0]["type"] == descriptor_pb2.FieldDescriptorProto.TYPE_STRING
        assert result[0]["type_name"] is None

    def test_type_name_extracts_last_segment(self, client: GrpcReflectionClient) -> None:
        msg = descriptor_pb2.DescriptorProto(name="User")
        field = msg.field.add()
        field.name = "profile"
        field.number = 2
        field.type = descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE
        field.type_name = ".test.v1.Profile"

        result = client.get_message_fields(msg)
        assert result[0]["type_name"] == "Profile"


class TestGetEnumValues:
    """Tests for get_enum_values."""

    def test_returns_values(self, client: GrpcReflectionClient) -> None:
        enum = descriptor_pb2.EnumDescriptorProto(name="Status")
        v1 = enum.value.add()
        v1.name = "ACTIVE"
        v1.number = 0
        v2 = enum.value.add()
        v2.name = "INACTIVE"
        v2.number = 1

        result = client.get_enum_values(enum)
        assert len(result) == 2
        assert result[0]["name"] == "ACTIVE"
        assert result[0]["number"] == 0
        assert result[1]["name"] == "INACTIVE"
        assert result[1]["number"] == 1


class TestGetPackageName:
    """Tests for get_package_name."""

    def test_returns_package(self, client: GrpcReflectionClient) -> None:
        proto_file = _make_proto_file(package="my.api.v1")
        assert client.get_package_name(proto_file) == "my.api.v1"

    def test_empty_package(self, client: GrpcReflectionClient) -> None:
        proto_file = _make_proto_file(package="")
        assert client.get_package_name(proto_file) == ""


class TestGetImports:
    """Tests for get_imports."""

    def test_imports_messages(self, client: GrpcReflectionClient) -> None:
        proto_file = _make_proto_file(name="test.proto")
        msg = proto_file.message_type.add()
        msg.name = "User"
        msg2 = proto_file.message_type.add()
        msg2.name = "Account"

        imports = client.get_imports(proto_file)
        assert any("from test_pb2 import User, Account" in i for i in imports)

    def test_imports_google_protobuf_deps(self, client: GrpcReflectionClient) -> None:
        proto_file = _make_proto_file()
        proto_file.dependency.append("google/protobuf/empty.proto")

        imports = client.get_imports(proto_file)
        assert any("from google.protobuf import empty_pb2" in i for i in imports)

    def test_imports_other_deps_as_relative(self, client: GrpcReflectionClient) -> None:
        proto_file = _make_proto_file()
        proto_file.dependency.append("other/types.proto")

        imports = client.get_imports(proto_file)
        assert any("from . import types_pb2" in i for i in imports)


class TestGetServices:
    """Tests for get_services."""

    def test_returns_services_with_methods(self, client: GrpcReflectionClient) -> None:
        proto_file = _make_proto_file(package="my.api")
        svc = proto_file.service.add()
        svc.name = "UserService"
        method = svc.method.add()
        method.name = "GetUser"
        method.input_type = ".my.api.GetUserRequest"
        method.output_type = ".my.api.GetUserResponse"

        result = client.get_services(proto_file)
        assert len(result) == 1
        assert result[0]["name"] == "UserService"
        assert result[0]["full_name"] == "my.api.UserService"
        assert len(result[0]["methods"]) == 1

    def test_empty_when_no_services(self, client: GrpcReflectionClient) -> None:
        proto_file = _make_proto_file()
        assert client.get_services(proto_file) == []


class TestGetMessages:
    """Tests for get_messages."""

    def test_returns_messages_with_fields(self, client: GrpcReflectionClient) -> None:
        proto_file = _make_proto_file()
        msg = proto_file.message_type.add()
        msg.name = "User"
        field = msg.field.add()
        field.name = "id"
        field.number = 1
        field.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING

        result = client.get_messages(proto_file)
        assert len(result) == 1
        assert result[0]["name"] == "User"
        assert len(result[0]["fields"]) == 1

    def test_empty_when_no_messages(self, client: GrpcReflectionClient) -> None:
        proto_file = _make_proto_file()
        assert client.get_messages(proto_file) == []


class TestGetEnums:
    """Tests for get_enums."""

    def test_returns_enums(self, client: GrpcReflectionClient) -> None:
        proto_file = _make_proto_file()
        enum = proto_file.enum_type.add()
        enum.name = "Status"
        v = enum.value.add()
        v.name = "ACTIVE"
        v.number = 0

        result = client.get_enums(proto_file)
        assert len(result) == 1
        assert result[0]["name"] == "Status"
        assert len(result[0]["values"]) == 1

    def test_empty_when_no_enums(self, client: GrpcReflectionClient) -> None:
        proto_file = _make_proto_file()
        assert client.get_enums(proto_file) == []


class TestGetOutputFilename:
    """Tests for get_output_filename."""

    def test_default_suffix(self, client: GrpcReflectionClient) -> None:
        proto_file = _make_proto_file(name="service.proto")
        assert client.get_output_filename(proto_file) == "service_pb2_pbreflect.py"

    def test_custom_suffix(self, client: GrpcReflectionClient) -> None:
        proto_file = _make_proto_file(name="service.proto")
        assert client.get_output_filename(proto_file, suffix="_custom.py") == "service_custom.py"

    def test_replaces_dashes(self, client: GrpcReflectionClient) -> None:
        proto_file = _make_proto_file(name="my-service.proto")
        assert client.get_output_filename(proto_file) == "my_service_pb2_pbreflect.py"


class TestGetProtoDescriptors:
    """Tests for get_proto_descriptors with caching."""

    def test_returns_cached_descriptors(self) -> None:
        client = GrpcReflectionClient(channel=None)
        client._descriptors = {"a.proto": _make_proto_file(name="a.proto")}
        result = client.get_proto_descriptors()
        assert "a.proto" in result
