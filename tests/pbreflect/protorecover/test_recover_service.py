"""Tests for RecoverService public methods."""

import socket
from pathlib import Path
from unittest.mock import MagicMock, create_autospec, patch

import pytest
from google.protobuf import descriptor_pb2

from pbreflect.protorecover.recover_service import (
    ProtoRecoveryError,
    RecoverService,
    RecoverServiceConnectionError,
)


class TestParseTarget:
    """Tests for RecoverService._parse_target."""

    def test_valid_target(self) -> None:
        host, port = RecoverService._parse_target("localhost:50051")
        assert host == "localhost"
        assert port == "50051"

    def test_invalid_target_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Invalid target format"):
            RecoverService._parse_target("invalid-no-port")


class TestRecoverProtoFiles:
    """Tests for RecoverService.recover_proto_files."""

    @patch("pbreflect.protorecover.recover_service.RecoverService._create_channel_safe")
    @patch("pbreflect.protorecover.recover_service.socket.getaddrinfo")
    def test_writes_proto_files_to_output_dir(
        self,
        mock_getaddrinfo: MagicMock,
        mock_channel: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_getaddrinfo.return_value = [(None, None, None, None, ("127.0.0.1", 50051))]
        mock_channel.return_value = MagicMock()

        service = RecoverService("localhost:50051", output_dir=tmp_path)

        descriptor = descriptor_pb2.FileDescriptorProto(
            name="test.proto",
            package="test.v1",
            syntax="proto3",
        )

        mock_reflection = create_autospec(service._reflection_client.__class__, instance=True)
        mock_reflection.get_proto_descriptors.return_value = {"test.proto": descriptor}
        service._reflection_client = mock_reflection

        result = service.recover_proto_files()
        assert len(result) == 1
        assert result[0] == tmp_path / "test.proto"
        assert (tmp_path / "test.proto").exists()
        assert 'syntax = "proto3"' in (tmp_path / "test.proto").read_text()

    @patch("pbreflect.protorecover.recover_service.RecoverService._create_channel_safe")
    @patch("pbreflect.protorecover.recover_service.socket.getaddrinfo")
    def test_returns_empty_when_no_descriptors(
        self,
        mock_getaddrinfo: MagicMock,
        mock_channel: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_getaddrinfo.return_value = [(None, None, None, None, ("127.0.0.1", 50051))]
        mock_channel.return_value = MagicMock()

        service = RecoverService("localhost:50051", output_dir=tmp_path)

        mock_reflection = create_autospec(service._reflection_client.__class__, instance=True)
        mock_reflection.get_proto_descriptors.return_value = {}
        service._reflection_client = mock_reflection

        result = service.recover_proto_files()
        assert result == []

    @patch("pbreflect.protorecover.recover_service.RecoverService._create_channel_safe")
    @patch("pbreflect.protorecover.recover_service.socket.getaddrinfo")
    def test_raises_proto_recovery_error_on_failure(
        self,
        mock_getaddrinfo: MagicMock,
        mock_channel: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_getaddrinfo.return_value = [(None, None, None, None, ("127.0.0.1", 50051))]
        mock_channel.return_value = MagicMock()

        service = RecoverService("localhost:50051", output_dir=tmp_path)

        mock_reflection = create_autospec(service._reflection_client.__class__, instance=True)
        mock_reflection.get_proto_descriptors.side_effect = RuntimeError("connection lost")
        service._reflection_client = mock_reflection

        with pytest.raises(ProtoRecoveryError, match="Failed to recover proto files"):
            service.recover_proto_files()


class TestGetServices:
    """Tests for RecoverService.get_services."""

    @patch("pbreflect.protorecover.recover_service.RecoverService._create_channel_safe")
    @patch("pbreflect.protorecover.recover_service.socket.getaddrinfo")
    def test_returns_service_info(
        self,
        mock_getaddrinfo: MagicMock,
        mock_channel: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_getaddrinfo.return_value = [(None, None, None, None, ("127.0.0.1", 50051))]
        mock_channel.return_value = MagicMock()

        service = RecoverService("localhost:50051", output_dir=tmp_path)

        descriptor = descriptor_pb2.FileDescriptorProto(
            name="test.proto",
            package="test.v1",
        )
        svc = descriptor.service.add()
        svc.name = "UserService"
        method = svc.method.add()
        method.name = "GetUser"
        method.input_type = ".test.v1.GetUserRequest"
        method.output_type = ".test.v1.GetUserResponse"

        mock_reflection = create_autospec(service._reflection_client.__class__, instance=True)
        mock_reflection.get_proto_descriptors.return_value = {"test.proto": descriptor}
        service._reflection_client = mock_reflection

        result = service.get_services()
        assert len(result) == 1
        assert result[0]["name"] == "UserService"
        assert result[0]["full_name"] == "test.v1.UserService"
        assert len(result[0]["methods"]) == 1
        assert result[0]["methods"][0]["name"] == "GetUser"

    @patch("pbreflect.protorecover.recover_service.RecoverService._create_channel_safe")
    @patch("pbreflect.protorecover.recover_service.socket.getaddrinfo")
    def test_returns_empty_on_error(
        self,
        mock_getaddrinfo: MagicMock,
        mock_channel: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_getaddrinfo.return_value = [(None, None, None, None, ("127.0.0.1", 50051))]
        mock_channel.return_value = MagicMock()

        service = RecoverService("localhost:50051", output_dir=tmp_path)

        mock_reflection = create_autospec(service._reflection_client.__class__, instance=True)
        mock_reflection.get_proto_descriptors.side_effect = RuntimeError("fail")
        service._reflection_client = mock_reflection

        assert service.get_services() == []


class TestContextManager:
    """Tests for RecoverService context manager protocol."""

    @patch("pbreflect.protorecover.recover_service.RecoverService._create_channel_safe")
    @patch("pbreflect.protorecover.recover_service.socket.getaddrinfo")
    def test_context_manager_closes_channel(
        self,
        mock_getaddrinfo: MagicMock,
        mock_channel: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_getaddrinfo.return_value = [(None, None, None, None, ("127.0.0.1", 50051))]
        mock_channel_obj = MagicMock()
        mock_channel.return_value = mock_channel_obj

        with RecoverService("localhost:50051", output_dir=tmp_path) as service:
            assert service is not None

        mock_channel_obj.close.assert_called_once()


class TestConnectionErrors:
    """Tests for connection error handling."""

    def test_dns_failure_raises_connection_error(self) -> None:
        with (
            patch("pbreflect.protorecover.recover_service.socket.getaddrinfo") as mock_getaddrinfo,
            pytest.raises(RecoverServiceConnectionError, match="DNS lookup failed"),
        ):
            mock_getaddrinfo.side_effect = socket.gaierror("not found")
            RecoverService("nonexistent.invalid:50051")

    def test_invalid_target_format_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Invalid target format"):
            RecoverService("no-port-here")
