#!/usr/bin/env python3
import sys
import re
import os
from jinja2 import Environment, FileSystemLoader
from google.protobuf.compiler import plugin_pb2 as plugin


def to_snake_case(name: str) -> str:
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def parse_parameters(param_string: str) -> dict:
    """Парсим параметры, например: async=true,suffix=_o3"""
    options = {}
    if param_string:
        for part in param_string.split(","):
            if "=" in part:
                key, value = part.split("=", 1)
                options[key.strip()] = value.strip()
            else:
                options[part.strip()] = "true"
    return options


def main():
    env = Environment(
        loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    client_template = env.get_template("client.jinja2")
    server_template = env.get_template("server.jinja2")

    data = sys.stdin.buffer.read()
    request = plugin.CodeGeneratorRequest()

    request.ParseFromString(data)

    response = plugin.CodeGeneratorResponse()
    response.supported_features = plugin.CodeGeneratorResponse.FEATURE_PROTO3_OPTIONAL

    # Читаем параметры
    options = parse_parameters(request.parameter)
    async_mode = options.get("async", "false").lower() == "true"
    suffix = options.get("suffix", "o3")  # например, o3

    for proto_file in request.proto_file:
        if not proto_file.service:
            continue

        for service in proto_file.service:
            methods = []
            for method in service.method:
                methods.append(
                    {
                        "original_name": method.name,
                        "snake_case_name": to_snake_case(method.name),
                        "input_type": method.input_type.split(".")[-1],
                        "output_type": method.output_type.split(".")[-1],
                    }
                )

            service_name_snake = to_snake_case(service.name)

            # Генерация клиента
            client_code = client_template.render(
                service_name=service.name,
                methods=methods,
                async_mode=async_mode,
            )

            client_file = response.file.add()
            client_file.name = proto_file.name.replace(
                ".proto", f"_{service_name_snake}_client.{suffix}.py"
            )
            client_file.content = client_code

            # Генерация сервера
            server_code = server_template.render(
                service_name=service.name,
                methods=methods,
                async_mode=async_mode,
            )

            server_file = response.file.add()
            server_file.name = proto_file.name.replace(
                ".proto", f"_{service_name_snake}_server.{suffix}.py"
            )
            server_file.content = server_code

    sys.stdout.buffer.write(response.SerializeToString())


if __name__ == "__main__":
    main()
