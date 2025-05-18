import logging
import socket
from pathlib import Path
from types import TracebackType
from typing import (
    ClassVar,
    final,
)

import grpc
from grpc import Channel, ChannelCredentials

from pbreflect.protorecover.proto_builder import ProtoFileBuilder
from pbreflect.protorecover.reflection_client import GrpcReflectionClient


class RecoverServiceConnectionError(Exception):
    """Custom exception for connection-related errors."""


class ProtoRecoveryError(Exception):
    """Custom exception for proto recovery errors."""


@final
class RecoverService:
    """Service for recovering protocol buffer definitions from gRPC servers using reflection.

    This service connects to a gRPC server, retrieves proto descriptors using the reflection API,
    and generates .proto files that can be used for client development.
    """

    DEFAULT_TIMEOUT: ClassVar[int] = 10

    def __init__(
        self,
        target: str,
        output_dir: Path | None = None,
        use_tls: bool = False,
        root_certificates_path: Path | None = None,
        private_key_path: Path | None = None,
        certificate_chain_path: Path | None = None,
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
        root_certificates_path: Path | None = None,
        private_key_path: Path | None = None,
        certificate_chain_path: Path | None = None,
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
            raise RecoverServiceConnectionError(f"Failed to establish channel to {target}: {e}") from e

    @staticmethod
    def _parse_target(target: str) -> tuple[str, str]:
        """Parse target into host and port components."""
        try:
            host, port = target.split(":")
            return host, port
        except ValueError as err:
            raise ValueError(f"Invalid target format '{target}'. Expected 'host:port'") from err

    @staticmethod
    def _validate_connection(host: str, port: str) -> None:
        """Validate that the host:port is reachable."""
        try:
            socket.getaddrinfo(host, port)
        except socket.gaierror as e:
            raise RecoverServiceConnectionError(f"DNS lookup failed for {host}:{port}: {e}") from e

    @staticmethod
    def _create_secure_channel(
        target: str,
        timeout: int,
        root_certificates_path: Path | None = None,
        private_key_path: Path | None = None,
        certificate_chain_path: Path | None = None,
    ) -> Channel:
        """Create and validate a secure gRPC channel."""
        try:
            root_certificates = None
            private_key = None
            certificate_chain = None

            if root_certificates_path:
                if not root_certificates_path.exists():
                    raise FileNotFoundError(f"Root certificates file not found: {root_certificates_path}")
                with open(root_certificates_path, "rb") as f:
                    root_certificates = f.read()

            if private_key_path:
                if not private_key_path.exists():
                    raise FileNotFoundError(f"Private key file not found: {private_key_path}")
                with open(private_key_path, "rb") as f:
                    private_key = f.read()

            if certificate_chain_path:
                if not certificate_chain_path.exists():
                    raise FileNotFoundError(f"Certificate chain file not found: {certificate_chain_path}")
                with open(certificate_chain_path, "rb") as f:
                    certificate_chain = f.read()

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
            raise RecoverServiceConnectionError(f"Secure channel creation failed: {e}") from e

    @staticmethod
    def _create_insecure_channel(target: str, timeout: int) -> Channel:
        """Create and validate an insecure gRPC channel."""
        try:
            channel = grpc.insecure_channel(target)
            grpc.channel_ready_future(channel).result(timeout=timeout)
            return channel
        except Exception as e:
            raise RecoverServiceConnectionError(f"Insecure channel creation failed: {e}") from e

    def __enter__(self) -> "RecoverService":
        """Context manager entry point."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit point."""
        self.close()

    def close(self) -> None:
        """Close the gRPC channel."""
        if hasattr(self, "_channel") and self._channel:
            self._channel.close()
            self._logger.info("gRPC channel closed")

    def recover_proto_files(self) -> list[Path]:
        """Recover proto files from the gRPC server.

        Returns:
            List of paths to the generated proto files

        Raises:
            ProtoRecoveryError: If proto recovery fails
        """
        try:
            self._logger.info("Starting proto file recovery")
            descriptors = self._reflection_client.get_proto_descriptors()

            if not descriptors:
                self._logger.warning("No proto descriptors found")
                return []

            self._logger.info(f"Found {len(descriptors)} proto descriptors")

            output_files = []
            for name, descriptor in descriptors.items():
                name, proto_content = self._proto_builder.get_proto(descriptor)

                output_path = self._output_dir / name
                output_path.parent.mkdir(parents=True, exist_ok=True)

                with open(output_path, "w") as f:
                    f.write(proto_content)

                output_files.append(output_path)
                self._logger.info(f"Generated proto file: {output_path}")

            return output_files
        except Exception as e:
            error_msg = f"Failed to recover proto files: {e}"
            self._logger.error(error_msg)
            raise ProtoRecoveryError(error_msg) from e

    def get_services(self) -> list[dict]:
        """Get information about all services exposed by the server.

        Returns:
            List of dictionaries with service information
        """
        try:
            descriptors = self._reflection_client.get_proto_descriptors()
            services = []

            for file_name, descriptor in descriptors.items():
                if descriptor.service:
                    for service in descriptor.service:
                        methods = []
                        for method in service.method:
                            methods.append(
                                {
                                    "name": method.name,
                                    "input_type": method.input_type,
                                    "output_type": method.output_type,
                                    "client_streaming": method.client_streaming,
                                    "server_streaming": method.server_streaming,
                                }
                            )

                        services.append(
                            {
                                "name": service.name,
                                "full_name": f"{descriptor.package}.{service.name}",
                                "file_name": file_name,
                                "methods": methods,
                            }
                        )

            return services
        except Exception as e:
            self._logger.error(f"Failed to get services: {e}")
            return []
