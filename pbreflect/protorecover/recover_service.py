from types import TracebackType

import grpc
from grpc import Channel
import google.protobuf.descriptor_pb2 as descriptor_pb2

import pathlib
import socket
from typing import (
    Optional,
    Tuple,
    Type,
)
import logging

from pbreflect.protorecover.proto_builder import ProtoFileBuilder
from pbreflect.protorecover.reflection_client import GrpcReflectionClient


class ConnectionError(Exception):
    """Custom exception for connection-related errors."""

    pass


class ProtoRecoveryError(Exception):
    """Custom exception for proto recovery errors."""

    pass


class RecoverService:
    def __init__(self, target: str, output_dir: Optional[pathlib.Path] = None):
        """Initialize the proto recovery service.

        Args:
            target: gRPC server target in format 'host:port'
            output_dir: Directory to save recovered proto files. Defaults to current working directory.
        """
        self._channel: Channel = self._create_channel_safe(target=target)
        self._reflection_client = GrpcReflectionClient(channel=self._channel)
        self._proto_builder = ProtoFileBuilder()
        self._output_dir = output_dir or pathlib.Path.cwd()
        self._logger = self._setup_logger()

    @staticmethod
    def _setup_logger() -> logging.Logger:
        """Configure and return a logger instance."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)

        if not logger.handlers:
            logger.addHandler(handler)

        return logger

    @staticmethod
    def _create_channel_safe(
        target: str,
        *,
        use_tls: bool = False,
        timeout: int = 10,
    ) -> Channel:
        """Create a gRPC channel with safety checks.

        Args:
            target: Server address in 'host:port' format
            use_tls: Whether to use TLS/SSL
            timeout: Connection timeout in seconds

        Returns:
            Established gRPC channel

        Raises:
            ConnectionError: If connection cannot be established
        """
        host, port = RecoverService._parse_target(target)
        RecoverService._validate_connection(host, port)

        try:
            if use_tls:
                return RecoverService._create_secure_channel(target, timeout)
            return RecoverService._create_insecure_channel(target, timeout)
        except grpc.RpcError as e:
            raise ConnectionError(f"Failed to establish channel to {target}: {e}")

    @staticmethod
    def _parse_target(target: str) -> Tuple[str, str]:
        """Parse target into host and port components."""
        try:
            host, port = target.split(":")
            return host, port
        except ValueError:
            raise ValueError(f"Invalid target format '{target}'. Expected 'host:port'")

    @staticmethod
    def _validate_connection(host: str, port: str) -> None:
        """Validate that the host:port is reachable."""
        try:
            socket.getaddrinfo(host, port)
        except socket.gaierror as e:
            raise ConnectionError(f"DNS lookup failed for {host}:{port}: {e}")

    @staticmethod
    def _create_secure_channel(target: str, timeout: int) -> Channel:
        """Create and validate a secure gRPC channel."""
        try:
            credentials = grpc.ssl_channel_credentials()
            channel = grpc.secure_channel(target, credentials)
            grpc.channel_ready_future(channel).result(timeout=timeout)
            return channel
        except Exception as e:
            raise ConnectionError(f"Secure channel creation failed: {e}")

    @staticmethod
    def _create_insecure_channel(target: str, timeout: int) -> Channel:
        """Create and validate an insecure gRPC channel."""
        channel = grpc.insecure_channel(target)
        grpc.channel_ready_future(channel).result(timeout=timeout)
        return channel

    def recover_protos(self) -> None:
        """Recover all proto files from the gRPC server."""
        try:
            descriptors = self._reflection_client.get_proto_descriptors()
            if not descriptors:
                self._logger.warning("No proto descriptors found on the server")
                return

            for proto_descriptor in descriptors.values():
                self._process_proto_descriptor(proto_descriptor)
        except Exception as e:
            self._logger.error(f"Proto recovery failed: {e}")
            raise ProtoRecoveryError("Failed to recover proto files") from e

    def _process_proto_descriptor(
        self, descriptor: descriptor_pb2.FileDescriptorProto
    ) -> None:
        """Process a single proto descriptor."""
        self._logger.info(f"Recovering proto: {descriptor.name}")
        try:
            name, content = self._proto_builder.get_proto(descriptor=descriptor)
            saved_path = self._write_proto_file(name, content)
            self._logger.info(f"Successfully saved proto to {saved_path}")
        except Exception as e:
            self._logger.error(f"Failed to recover {descriptor.name}: {e}")
            raise

    def _write_proto_file(self, name: str, content: str) -> pathlib.Path:
        """Write proto content to a file.

        Args:
            name: Proto file name (may include package path)
            content: Proto file content

        Returns:
            Path to the saved file
        """
        file_path = self._build_file_path(name)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return file_path
        except IOError as e:
            self._logger.error(f"Failed to write proto file {name}: {e}")
            raise

    def _build_file_path(self, name: str) -> pathlib.Path:
        """Construct the full file path from proto name."""
        parts = name.rsplit(".", 1)
        if len(parts) == 1:
            directory = parts[0].replace(".", "/")
            return self._output_dir / directory

        directory, filename = parts
        # TODO: непонятно надо ли преобразовывать пути
        # directory = directory.replace(".", "/")
        return self._output_dir / f"{directory}.{filename}"

    def close(self) -> None:
        """Clean up resources."""
        if hasattr(self, "_channel"):
            self._channel.close()
            self._logger.info("gRPC channel closed")

    def __enter__(self) -> "RecoverService":
        """Support for context manager protocol."""
        return self

    def __exit__(
        self,
        exc_type: Type[BaseException],
        exc_val: BaseException,
        exc_tb: TracebackType,
    ) -> None:
        """Ensure resources are cleaned up when exiting context."""
        self.close()
