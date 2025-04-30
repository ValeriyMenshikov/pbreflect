import grpc
from grpc_reflection.v1alpha import reflection_pb2, reflection_pb2_grpc
from google.protobuf import descriptor_pb2


class GrpcReflectionClient:
    def __init__(self, channel: grpc.Channel):
        self._stub = reflection_pb2_grpc.ServerReflectionStub(channel)
        self._descriptors: dict[str, descriptor_pb2.FileDescriptorProto] = {}

    def get_proto_descriptors(self) -> dict[str, descriptor_pb2.FileDescriptorProto]:
        if not self._descriptors:
            self._load_and_cache_descriptors()
        return self._descriptors

    def _load_and_cache_descriptors(self) -> None:
        service_names = self._discover_services()
        for name in service_names:
            self._resolve_service_descriptors(name)

    def _discover_services(self) -> list[str]:
        request = reflection_pb2.ServerReflectionRequest(list_services="")
        response = self._stub.ServerReflectionInfo(iter([request]))
        return [s.name for s in next(response).list_services_response.service]

    def _resolve_service_descriptors(self, service_name: str) -> None:
        request = reflection_pb2.ServerReflectionRequest(
            file_containing_symbol=service_name
        )
        response = self._stub.ServerReflectionInfo(iter([request]))
        self._parse_file_descriptors(next(response))

    def _parse_file_descriptors(
        self, response: reflection_pb2.ServerReflectionResponse
    ) -> None:
        for proto_bytes in response.file_descriptor_response.file_descriptor_proto:
            descriptor = descriptor_pb2.FileDescriptorProto()
            descriptor.ParseFromString(proto_bytes)
            self._descriptors[descriptor.name] = descriptor
