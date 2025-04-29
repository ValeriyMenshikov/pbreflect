import pathlib
from typing import Iterable

import grpc
from grpc_reflection.v1alpha import reflection_pb2, reflection_pb2_grpc
from google.protobuf import descriptor_pb2


class GrpcReflectionClient:
    def __init__(
        self,
        channel: grpc.Channel,
    ) -> None:
        self._channel = channel
        self._reflection_stub = reflection_pb2_grpc.ServerReflectionStub(self._channel)
        self.stub_names: set[str] = set()
        self.proto_file_descriptors: dict[str, descriptor_pb2.FileDescriptorProto] = {}

    def _extract(self) -> None:
        services = self._get_stub_names()
        self._fetch_proto_files(services)

    def _get_stub_names(self) -> list[str]:
        services_response = self._reflection_stub.ServerReflectionInfo(
            iter([reflection_pb2.ServerReflectionRequest(list_services="")])
        )
        full_stub_names = [
            service.name
            for service in next(services_response).list_services_response.service
        ]
        self.stub_names = {name.split(".")[-1] for name in full_stub_names}
        return full_stub_names

    def _fetch_proto_files(self, full_stub_names: list[str]) -> None:
        for service_name in full_stub_names:
            file_protos = self._get_file_protos(service_name)
            for file_proto_response in file_protos:
                self._process_proto_response(file_proto_response)

    def _get_file_protos(
        self, stub_name: str
    ) -> Iterable[reflection_pb2.ServerReflectionResponse]:
        file_symbol_requests = [
            reflection_pb2.ServerReflectionRequest(file_containing_symbol=stub_name)
        ]
        return self._reflection_stub.ServerReflectionInfo(iter(file_symbol_requests))

    def _process_proto_response(
        self, file_proto_response: reflection_pb2.ServerReflectionResponse
    ) -> None:
        for (
            proto_bytes
        ) in file_proto_response.file_descriptor_response.file_descriptor_proto:
            file_descriptor_proto = descriptor_pb2.FileDescriptorProto()
            file_descriptor_proto.ParseFromString(proto_bytes)
            self.proto_file_descriptors[file_descriptor_proto.name] = (
                file_descriptor_proto
            )

    def get_descriptors(self) -> dict[str, descriptor_pb2.FileDescriptorProto]:
        self._extract()
        return self.proto_file_descriptors
