"""Tests for ProtoFileBuilder."""

import google.protobuf.descriptor_pb2 as descriptor_pb2
import pytest

from pbreflect.protorecover.proto_builder import ProtoFileBuilder


@pytest.fixture
def builder() -> ProtoFileBuilder:
    return ProtoFileBuilder()


def _make_descriptor(
    name: str = "test.proto",
    package: str = "test.v1",
    syntax: str = "proto3",
) -> descriptor_pb2.FileDescriptorProto:
    return descriptor_pb2.FileDescriptorProto(
        name=name,
        package=package,
        syntax=syntax,
    )


class TestGetProto:
    """Tests for ProtoFileBuilder.get_proto."""

    def test_returns_tuple_of_name_and_content(self, builder: ProtoFileBuilder) -> None:
        descriptor = _make_descriptor(name="my_service.proto", package="my.api")
        name, content = builder.get_proto(descriptor)
        assert name == "my_service.proto"
        assert isinstance(content, str)
        assert 'syntax = "proto3"' in content
        assert 'package my.api;' in content

    def test_defaults_to_proto2_when_syntax_empty(self, builder: ProtoFileBuilder) -> None:
        descriptor = _make_descriptor(syntax="")
        _, content = builder.get_proto(descriptor)
        assert 'syntax = "proto2"' in content

    def test_strips_leading_dots_from_name(self, builder: ProtoFileBuilder) -> None:
        descriptor = _make_descriptor(name="./../weird.proto")
        name, _ = builder.get_proto(descriptor)
        assert ".." not in name
        assert name == "weird.proto"

    def test_renders_service(self, builder: ProtoFileBuilder) -> None:
        descriptor = _make_descriptor(package="my.api")
        service = descriptor.service.add()
        service.name = "UserService"
        method = service.method.add()
        method.name = "GetUser"
        method.input_type = ".my.api.GetUserRequest"
        method.output_type = ".my.api.GetUserResponse"

        _, content = builder.get_proto(descriptor)
        assert "service UserService" in content
        assert "GetUser" in content
        assert "GetUserRequest" in content
        assert "GetUserResponse" in content

    def test_renders_message_with_fields(self, builder: ProtoFileBuilder) -> None:
        descriptor = _make_descriptor(package="my.api")
        msg = descriptor.message_type.add()
        msg.name = "User"
        field = msg.field.add()
        field.name = "id"
        field.number = 1
        field.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING
        field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL

        _, content = builder.get_proto(descriptor)
        assert "message User" in content
        assert "string id" in content

    def test_renders_enum(self, builder: ProtoFileBuilder) -> None:
        descriptor = _make_descriptor(package="my.api")
        enum = descriptor.enum_type.add()
        enum.name = "Status"
        val = enum.value.add()
        val.name = "ACTIVE"
        val.number = 0
        val2 = enum.value.add()
        val2.name = "INACTIVE"
        val2.number = 1

        _, content = builder.get_proto(descriptor)
        assert "enum Status" in content
        assert "ACTIVE" in content
        assert "INACTIVE" in content

    def test_renders_imports(self, builder: ProtoFileBuilder) -> None:
        descriptor = _make_descriptor()
        descriptor.dependency.append("google/protobuf/empty.proto")
        _, content = builder.get_proto(descriptor)
        assert "import" in content
        assert "google/protobuf/empty.proto" in content

    def test_normalizes_malformed_dependency(self, builder: ProtoFileBuilder) -> None:
        descriptor = _make_descriptor()
        descriptor.dependency.append("foo/bar/gitlab.example.com/x/y.proto")
        _, content = builder.get_proto(descriptor)
        assert "gitlab.example.com/x/y.proto" in content


class TestNormalizeDependencyImport:
    """Tests for _normalize_dependency_import static method."""

    def test_single_domain_returns_as_is(self) -> None:
        result = ProtoFileBuilder._normalize_dependency_import("gitlab.example.com/x/y.proto")
        assert result == "gitlab.example.com/x/y.proto"

    def test_multiple_domains_keeps_last(self) -> None:
        result = ProtoFileBuilder._normalize_dependency_import(
            "gitlab.example.com/foo/bar/gitlab2.example.com/x/y.proto"
        )
        assert result == "gitlab2.example.com/x/y.proto"

    def test_no_domain_returns_as_is(self) -> None:
        result = ProtoFileBuilder._normalize_dependency_import("simple/path.proto")
        assert result == "simple/path.proto"
