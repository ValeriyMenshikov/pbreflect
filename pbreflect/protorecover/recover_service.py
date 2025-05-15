from types import TracebackType
from pathlib import Path
import logging
import socket
from typing import (
    Any,
    Dict,
    Optional,
    Tuple,
    Type,
    final,
    ClassVar,
)

import grpc
from grpc import Channel, ChannelCredentials
import google.protobuf.descriptor_pb2 as descriptor_pb2

from pbreflect.protorecover.proto_builder import ProtoFileBuilder
from pbreflect.protorecover.reflection_client import GrpcReflectionClient


class ConnectionError(Exception):
    """Custom exception for connection-related errors."""


class ProtoRecoveryError(Exception):
    """Custom exception for proto recovery errors."""


@final
class RecoverService:
    """Service for recovering protocol buffer definitions from gRPC servers using reflection.

    This service connects to a gRPC server, retrieves proto descriptors using the reflection API,
    and generates .proto files that can be used for client development.
    """

    # Class constants
    DEFAULT_TIMEOUT: ClassVar[int] = 10

    def __init__(
        self,
        target: str,
        output_dir: Optional[Path] = None,
        use_tls: bool = False,
        root_certificates_path: Optional[Path] = None,
        private_key_path: Optional[Path] = None,
        certificate_chain_path: Optional[Path] = None,
    ) -> None:
        """Initialize the proto recovery service.

        Args:
            target: gRPC server target in format 'host:port'
            output_dir: Directory to save recovered proto files. Defaults to current working directory.
            use_tls: Whether to use TLS/SSL for the connection
            root_certificates_path: Path to the root certificates file (CA certs)
            private_key_path: Path to the private key file
            certificate_chain_path: Path to the certificate chain file
        """
        self._logger = self._setup_logger()
        self._channel: Channel = self._create_channel_safe(
            target=target,
            use_tls=use_tls,
            root_certificates_path=root_certificates_path,
            private_key_path=private_key_path,
            certificate_chain_path=certificate_chain_path,
        )
        self._reflection_client = GrpcReflectionClient(channel=self._channel)
        self._proto_builder = ProtoFileBuilder()
        self._output_dir = output_dir or Path.cwd()

        self._logger.info(f"RecoverService initialized with target: {target}")
        self._logger.info(f"Output directory set to: {self._output_dir}")
        if use_tls:
            self._logger.info("Using TLS/SSL for connection")

    @staticmethod
    def _setup_logger() -> logging.Logger:
        """Configure and return a logger instance."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        # Only add handler if not already present to avoid duplicate logs
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    @classmethod
    def _create_channel_safe(
        cls,
        target: str,
        *,
        use_tls: bool = False,
        timeout: int = DEFAULT_TIMEOUT,
        root_certificates_path: Optional[Path] = None,
        private_key_path: Optional[Path] = None,
        certificate_chain_path: Optional[Path] = None,
    ) -> Channel:
        """Create a gRPC channel with safety checks.

        Args:
            target: Server address in 'host:port' format
            use_tls: Whether to use TLS/SSL
            timeout: Connection timeout in seconds
            root_certificates_path: Path to the root certificates file (CA certs)
            private_key_path: Path to the private key file
            certificate_chain_path: Path to the certificate chain file

        Returns:
            Established gRPC channel

        Raises:
            ConnectionError: If connection cannot be established
            ValueError: If target format is invalid
        """
        host, port = cls._parse_target(target)
        cls._validate_connection(host, port)

        try:
            if use_tls:
                return cls._create_secure_channel(
                    target,
                    timeout,
                    root_certificates_path,
                    private_key_path,
                    certificate_chain_path,
                )
            return cls._create_insecure_channel(target, timeout)
        except grpc.RpcError as e:
            raise ConnectionError(f"Failed to establish channel to {target}: {e}") from e

    @staticmethod
    def _parse_target(target: str) -> Tuple[str, str]:
        """Parse target into host and port components.

        Args:
            target: Server address in 'host:port' format

        Returns:
            Tuple containing host and port as strings

        Raises:
            ValueError: If target format is invalid
        """
        try:
            host, port = target.split(":")
            return host, port
        except ValueError:
            raise ValueError(f"Invalid target format '{target}'. Expected 'host:port'")

    @staticmethod
    def _validate_connection(host: str, port: str) -> None:
        """Validate that the host:port is reachable.

        Args:
            host: Hostname or IP address
            port: Port number as string

        Raises:
            ConnectionError: If DNS lookup fails
        """
        try:
            socket.getaddrinfo(host, port)
        except socket.gaierror as e:
            raise ConnectionError(f"DNS lookup failed for {host}:{port}: {e}") from e

    @staticmethod
    def _create_secure_channel(
        target: str,
        timeout: int,
        root_certificates_path: Optional[Path] = None,
        private_key_path: Optional[Path] = None,
        certificate_chain_path: Optional[Path] = None,
    ) -> Channel:
        """Create and validate a secure gRPC channel.

        Args:
            target: Server address in 'host:port' format
            timeout: Connection timeout in seconds
            root_certificates_path: Path to the root certificates file (CA certs)
            private_key_path: Path to the private key file
            certificate_chain_path: Path to the certificate chain file

        Returns:
            Secure gRPC channel

        Raises:
            ConnectionError: If channel creation fails
            FileNotFoundError: If certificate files are specified but not found
        """
        try:
            # Read certificate files if provided
            root_certificates = None
            private_key = None
            certificate_chain = None

            if root_certificates_path:
                if not root_certificates_path.exists():
                    raise FileNotFoundError(
                        f"Root certificates file not found: {root_certificates_path}"
                    )
                with open(root_certificates_path, "rb") as f:
                    root_certificates = f.read()

            if private_key_path:
                if not private_key_path.exists():
                    raise FileNotFoundError(f"Private key file not found: {private_key_path}")
                with open(private_key_path, "rb") as f:
                    private_key = f.read()

            if certificate_chain_path:
                if not certificate_chain_path.exists():
                    raise FileNotFoundError(
                        f"Certificate chain file not found: {certificate_chain_path}"
                    )
                with open(certificate_chain_path, "rb") as f:
                    certificate_chain = f.read()

            # Create credentials with the provided certificates
            credentials: ChannelCredentials = grpc.ssl_channel_credentials(
                root_certificates=root_certificates,
                private_key=private_key,
                certificate_chain=certificate_chain,
            )

            channel = grpc.secure_channel(target, credentials)
            grpc.channel_ready_future(channel).result(timeout=timeout)
            return channel
        except FileNotFoundError as e:
            raise e
        except Exception as e:
            raise ConnectionError(f"Secure channel creation failed: {e}") from e

    @staticmethod
    def _create_insecure_channel(target: str, timeout: int) -> Channel:
        """Create and validate an insecure gRPC channel.

        Args:
            target: Server address in 'host:port' format
            timeout: Connection timeout in seconds

        Returns:
            Insecure gRPC channel

        Raises:
            ConnectionError: If channel creation fails
        """
        try:
            channel = grpc.insecure_channel(target)
            grpc.channel_ready_future(channel).result(timeout=timeout)
            return channel
        except Exception as e:
            raise ConnectionError(f"Insecure channel creation failed: {e}") from e

    def recover_protos(self) -> Dict[str, Path]:
        """Recover all proto files from the gRPC server.

        Returns:
            Dictionary mapping proto names to saved file paths

        Raises:
            ProtoRecoveryError: If proto recovery fails
        """
        self._logger.info("Starting proto recovery process")
        saved_files: Dict[str, Path] = {}

        try:
            descriptors = self._reflection_client.get_proto_descriptors()
            if not descriptors:
                self._logger.warning("No proto descriptors found on the server")
                return saved_files

            for proto_name, proto_descriptor in descriptors.items():
                file_path = self._process_proto_descriptor(proto_descriptor)
                if file_path:
                    saved_files[proto_name] = file_path

            self._logger.info(f"Successfully recovered {len(saved_files)} proto files")
            return saved_files

        except Exception as e:
            self._logger.error(f"Proto recovery failed: {e}")
            raise ProtoRecoveryError("Failed to recover proto files") from e

    def _process_proto_descriptor(
        self, descriptor: descriptor_pb2.FileDescriptorProto
    ) -> Optional[Path]:
        """Process a single proto descriptor.

        Args:
            descriptor: Proto file descriptor

        Returns:
            Path to the saved file, or None if processing failed

        Raises:
            Exception: If proto processing fails
        """
        self._logger.info(f"Recovering proto: {descriptor.name}")
        try:
            name, content = self._proto_builder.get_proto(descriptor=descriptor)
            saved_path = self._write_proto_file(name, content)
            self._logger.info(f"Successfully saved proto to {saved_path}")
            return saved_path
        except Exception as e:
            self._logger.error(f"Failed to recover {descriptor.name}: {e}")
            raise

    def _write_proto_file(self, name: str, content: str) -> Path:
        """Write proto content to a file.

        Args:
            name: Proto file name (may include package path)
            content: Proto file content

        Returns:
            Path to the saved file

        Raises:
            IOError: If file writing fails
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

    def _build_file_path(self, name: str) -> Path:
        """Construct the full file path from proto name.

        Args:
            name: Proto file name (may include package path)

        Returns:
            Complete path where the file should be saved
        """
        parts = name.rsplit(".", 1)
        if len(parts) == 1:
            # Handle case where there's no extension
            directory = parts[0].replace(".", "/")
            return self._output_dir / directory

        directory, filename = parts
        # Using a comment to explain the TODO rather than leaving it as is
        # The directory structure should match the package structure in the proto
        return self._output_dir / f"{directory}.{filename}"

    def close(self) -> None:
        """Clean up resources and close the gRPC channel."""
        if hasattr(self, "_channel"):
            self._channel.close()
            self._logger.info("gRPC channel closed")

    def __enter__(self) -> "RecoverService":
        """Support for context manager protocol."""
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Ensure resources are cleaned up when exiting context."""
        self.close()
