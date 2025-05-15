from typing import Dict, List, Iterator, Optional, final

import grpc
from grpc_reflection.v1alpha import reflection_pb2, reflection_pb2_grpc
from google.protobuf import descriptor_pb2


@final
class GrpcReflectionClient:
    """Client for interacting with gRPC reflection service.

    This client provides methods to discover services and retrieve proto descriptors
    from a gRPC server that has the reflection service enabled.
    """

    def __init__(self, channel: grpc.Channel) -> None:
        """Initialize the reflection client.

        Args:
            channel: An established gRPC channel to the server
        """
        self._stub = reflection_pb2_grpc.ServerReflectionStub(channel)
        self._descriptors: Dict[str, descriptor_pb2.FileDescriptorProto] = {}

    def get_proto_descriptors(self) -> Dict[str, descriptor_pb2.FileDescriptorProto]:
        """Retrieve all proto descriptors from the server.

        Returns:
            Dictionary mapping proto file names to their descriptors

        Raises:
            grpc.RpcError: If the reflection service call fails
        """
        if not self._descriptors:
            self._load_and_cache_descriptors()
        return self._descriptors

    def _load_and_cache_descriptors(self) -> None:
        """Load and cache all service descriptors from the server."""
        try:
            service_names = self._discover_services()
            if not service_names:
                return

            for name in service_names:
                self._resolve_service_descriptors(name)
        except grpc.RpcError as e:
            # Re-raise with more context
            raise grpc.RpcError(
                f"Failed to load descriptors: {e.details() if hasattr(e, 'details') else str(e)}"
            ) from e

    def _discover_services(self) -> List[str]:
        """Discover all services exposed by the server.

        Returns:
            List of fully-qualified service names

        Raises:
            grpc.RpcError: If the reflection service call fails
        """
        request = reflection_pb2.ServerReflectionRequest(list_services="")
        response_iterator = self._stub.ServerReflectionInfo(iter([request]))

        try:
            response = next(response_iterator)
            return [s.name for s in response.list_services_response.service]
        except StopIteration:
            return []

    def _resolve_service_descriptors(self, service_name: str) -> None:
        """Resolve and cache descriptors for a specific service.

        Args:
            service_name: Fully-qualified name of the service

        Raises:
            grpc.RpcError: If the reflection service call fails
        """
        request = reflection_pb2.ServerReflectionRequest(file_containing_symbol=service_name)
        response_iterator = self._stub.ServerReflectionInfo(iter([request]))

        try:
            response = next(response_iterator)
            self._parse_file_descriptors(response)
        except StopIteration:
            # No response received
            pass

    def _parse_file_descriptors(self, response: reflection_pb2.ServerReflectionResponse) -> None:
        """Parse file descriptors from a reflection response.

        Args:
            response: Server reflection response containing file descriptors
        """
        for proto_bytes in response.file_descriptor_response.file_descriptor_proto:
            descriptor = descriptor_pb2.FileDescriptorProto()
            descriptor.ParseFromString(proto_bytes)

            # Skip if we already have this descriptor
            if descriptor.name in self._descriptors:
                continue

            self._descriptors[descriptor.name] = descriptor

            # Recursively resolve dependencies if needed
            for dependency in descriptor.dependency:
                if dependency not in self._descriptors:
                    self._resolve_file_descriptor(dependency)

    def _resolve_file_descriptor(self, file_name: str) -> None:
        """Resolve and cache a specific file descriptor.

        Args:
            file_name: Name of the proto file to resolve
        """
        request = reflection_pb2.ServerReflectionRequest(file_by_filename=file_name)
        response_iterator = self._stub.ServerReflectionInfo(iter([request]))

        try:
            response = next(response_iterator)
            self._parse_file_descriptors(response)
        except StopIteration:
            # No response received
            pass
