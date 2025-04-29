from pgreflect.protorecover.proto_builder import ProtoFileBuilder
from pgreflect.protorecover.reflection_client import GrpcReflectionClient
import pathlib
import grpc
from grpc import Channel
import socket


class RecoverService:
    def __init__(self, target: str, output_dir: pathlib.Path = None):
        self._channel: grpc.Channel = self.create_channel_safe(target=target)
        self.reflection_client = GrpcReflectionClient(channel=self._channel)
        self.proto_builder = ProtoFileBuilder()
        self.output_dir = output_dir or pathlib.Path.cwd()

    @staticmethod
    def create_channel_safe(
        target: str,
        *,
        use_tls: bool = False,
        timeout: int = 10,
    ) -> Channel:
        """
        Создаёт gRPC канал с автоматическим выбором secure/insecure подключения.

        :param target: Адрес сервиса, например "example.com:50051"
        :param use_tls: Пытаться сразу через TLS? (по умолчанию False = через insecure)
        :param timeout: Таймаут для проверки доступности сервиса.
        :return: gRPC Channel
        """
        host, port = target.split(":")

        # Проверяем, доступен ли хост
        try:
            socket.getaddrinfo(host, port)
        except socket.gaierror as e:
            raise ConnectionError(f"DNS lookup failed for {target}: {e}")

        if use_tls:
            try:
                credentials = grpc.ssl_channel_credentials()
                channel = grpc.secure_channel(target, credentials)
                grpc.channel_ready_future(channel).result(timeout=timeout)
                return channel
            except Exception as e:
                print(
                    f"Secure channel to {target} failed, falling back to insecure: {e}"
                )

        channel = grpc.insecure_channel(target)
        grpc.channel_ready_future(channel).result(timeout=timeout)
        return channel

    def recover_protos(self) -> None:
        descriptors = self.reflection_client.get_descriptors()
        for proto_descriptor in descriptors.values():
            print(f"[INFO] Recovering proto: {proto_descriptor.name}")
            try:
                name, content = self.proto_builder.get_proto(
                    descriptor=proto_descriptor
                )
                self._write_proto_file(name, content)
            except Exception as e:
                print(f"[ERROR] Failed to recover {proto_descriptor.name}: {e}")

    def _write_proto_file(self, name, content):
        parts = name.rsplit(".", 1)
        directory = parts[0].replace(".", "/")
        new_path = directory if len(parts) == 1 else f"{directory}.{parts[1]}"
        proto_name = self.output_dir / new_path
        proto_name.parent.mkdir(parents=True, exist_ok=True)
        with open(proto_name, "w") as f:
            f.write(content)
        return proto_name
