import pathlib

from extractor import GrpcServiceExtractor
import grpc

# channel = grpc.insecure_channel("5.63.153.31:5055")
# channel = grpc.insecure_channel("pvz-api-inbound-release-pvz-21061.pvz-api-inbound.svc.stg-apps01-z502.k8s.o3.ru:82")
# g = GrpcServiceExtractor(channel)._recover_protos()


# channel = grpc.insecure_channel("pvz-api-inbound-release-pvz-21061.pvz-api-inbound.svc.stg-apps01-z502.k8s.o3.ru:82")
# channel = grpc.insecure_channel("5.63.153.31:5055")

import grpc
from grpc import Channel
import socket


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
            print(f"Secure channel to {target} failed, falling back to insecure: {e}")

    # Иначе — создаём обычный insecure канал
    channel = grpc.insecure_channel(target)
    grpc.channel_ready_future(channel).result(timeout=timeout)
    return channel


channel = create_channel_safe(
    target="10.227.44.235:82"
)
extractor = GrpcServiceExtractor(channel, output_dir=pathlib.Path("./recovered_protos"))
extractor.recover_protos()
