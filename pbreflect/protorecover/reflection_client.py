import re
from typing import final

import grpc
from google.protobuf import descriptor_pb2
from grpc_reflection.v1alpha import reflection_pb2, reflection_pb2_grpc


@final
class GrpcReflectionClient:
    """Client for interacting with gRPC reflection service.

    This client provides methods to discover services and retrieve proto descriptors
    from a gRPC server that has the reflection service enabled.
    """

    def __init__(self, channel: grpc.Channel | None) -> None:
        """Initialize the reflection client.

        Args:
            channel: An established gRPC channel to the server
        """
        self._stub = None
        if channel is not None:
            self._stub = reflection_pb2_grpc.ServerReflectionStub(channel)
        self._descriptors: dict[str, descriptor_pb2.FileDescriptorProto] = {}

    def get_proto_descriptors(self) -> dict[str, descriptor_pb2.FileDescriptorProto]:
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

    def _discover_services(self) -> list[str]:
        """Discover all services exposed by the server.

        Returns:
            List of fully-qualified service names

        Raises:
            grpc.RpcError: If the reflection service call fails
        """
        request = reflection_pb2.ServerReflectionRequest(list_services="")
        response_iterator = self._stub.ServerReflectionInfo(iter([request])) if self._stub else None

        if response_iterator is None:
            return []

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
        response_iterator = self._stub.ServerReflectionInfo(iter([request])) if self._stub else None

        if response_iterator is None:
            return

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

            # Recursively resolve dependencies
            for dependency in descriptor.dependency:
                if dependency not in self._descriptors:
                    self._resolve_file_descriptor(dependency)

    def _resolve_file_descriptor(self, file_name: str) -> None:
        """Resolve and cache a file descriptor by name.

        Args:
            file_name: Name of the proto file

        Raises:
            grpc.RpcError: If the reflection service call fails
        """
        request = reflection_pb2.ServerReflectionRequest(file_by_filename=file_name)
        response_iterator = self._stub.ServerReflectionInfo(iter([request])) if self._stub else None

        if response_iterator is None:
            return

        try:
            response = next(response_iterator)
            self._parse_file_descriptors(response)
        except StopIteration:
            # No response received
            pass

    # Дополнительные методы для работы с дескрипторами

    def _camel_to_snake(self, name: str) -> str:
        """Convert camelCase to snake_case.

        Args:
            name: Name in camelCase

        Returns:
            Name in snake_case
        """
        # Если имя начинается с заглавной буквы, приводим к нижнему регистру
        if name and name[0].isupper():
            name = name[0].lower() + name[1:]

        # Добавляем underscore перед каждой заглавной буквой и приводим к нижнему регистру
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def get_service_methods(self, service: descriptor_pb2.ServiceDescriptorProto) -> list[dict]:
        """Get methods from a service descriptor.

        Args:
            service: Service descriptor

        Returns:
            List of method information dictionaries
        """
        methods = []
        for method in service.method:
            # Сохраняем полный путь к типу (убираем начальную точку, если она есть)
            full_input_type = method.input_type[1:] if method.input_type.startswith(".") else method.input_type
            full_output_type = method.output_type[1:] if method.output_type.startswith(".") else method.output_type

            # Преобразуем полный путь к типу в путь к модулю Python
            input_type = self._get_python_type_path(full_input_type)
            output_type = self._get_python_type_path(full_output_type)

            # Определяем, является ли метод потоковым
            is_server_streaming = method.server_streaming
            is_client_streaming = method.client_streaming

            methods.append(
                {
                    "name": self._camel_to_snake(method.name),
                    "original_name": method.name,
                    "input_type": input_type,
                    "output_type": output_type,
                    "is_server_streaming": is_server_streaming,
                    "is_client_streaming": is_client_streaming,
                }
            )

        return methods

    def _get_python_type_path(self, proto_type_path: str) -> str:
        """Преобразует полный путь к типу protobuf в путь к модулю Python.

        Args:
            proto_type_path: Полный путь к типу в формате protobuf (например, 'google.protobuf.Empty')

        Returns:
            Путь к типу в формате Python (например, 'empty_pb2.Empty')
        """
        if not proto_type_path or "." not in proto_type_path:
            return proto_type_path

        # Разделяем путь на компоненты (убираем начальную точку, если она есть)
        path = proto_type_path[1:] if proto_type_path.startswith(".") else proto_type_path
        components = path.split(".")
        type_name = components[-1]  # Последний компонент - это имя типа

        # Для стандартных типов Google Protobuf используем соответствующий модуль
        if len(components) >= 3 and components[0] == "google" and components[1] == "protobuf":
            # Формируем имя модуля на основе последнего компонента (имени типа)
            # Например, для 'google.protobuf.Empty' -> 'empty_pb2.Empty'
            module_name = self._camel_to_snake(type_name).lower() + "_pb2"
            return f"{module_name}.{type_name}"

        # Для других типов возвращаем короткое имя для обратной совместимости
        return type_name

    def get_message_fields(self, message: descriptor_pb2.DescriptorProto) -> list[dict]:
        """Get fields from a message descriptor.

        Args:
            message: Message descriptor

        Returns:
            List of field information dictionaries
        """
        fields = []
        for field in message.field:
            fields.append(
                {
                    "name": field.name,
                    "number": field.number,
                    "type": field.type,
                    "type_name": field.type_name.split(".")[-1] if field.type_name else None,
                    "label": field.label,
                    "proto3_optional": field.proto3_optional if hasattr(field, "proto3_optional") else False,
                }
            )

        return fields

    def get_enum_values(self, enum: descriptor_pb2.EnumDescriptorProto) -> list[dict]:
        """Get values from an enum descriptor.

        Args:
            enum: Enum descriptor

        Returns:
            List of enum value information dictionaries
        """
        values = []
        for value in enum.value:
            values.append(
                {
                    "name": value.name,
                    "number": value.number,
                }
            )

        return values

    def get_nested_types(
        self,
        message: descriptor_pb2.DescriptorProto,
        prefix: str = "",
    ) -> list[dict]:
        """Get nested message types from a message descriptor.

        Args:
            message: Message descriptor
            prefix: Prefix for nested type names

        Returns:
            List of nested type information dictionaries
        """
        nested_types = []

        # Формируем префикс для вложенных типов
        type_prefix = f"{prefix}.{message.name}" if prefix else message.name

        # Обрабатываем вложенные сообщения
        for nested_message in message.nested_type:
            fields = self.get_message_fields(nested_message)
            nested_types.append(
                {
                    "name": nested_message.name,
                    "full_name": f"{type_prefix}.{nested_message.name}",
                    "fields": fields,
                }
            )

            # Рекурсивно обрабатываем вложенные типы
            nested_types.extend(self.get_nested_types(nested_message, type_prefix))

        return nested_types

    def get_nested_enums(
        self,
        message: descriptor_pb2.DescriptorProto,
        prefix: str = "",
    ) -> list[dict]:
        """Get nested enum types from a message descriptor.

        Args:
            message: Message descriptor
            prefix: Prefix for nested enum names

        Returns:
            List of nested enum information dictionaries
        """
        nested_enums = []

        # Формируем префикс для вложенных типов
        type_prefix = f"{prefix}.{message.name}" if prefix else message.name

        # Обрабатываем вложенные перечисления
        for nested_enum in message.enum_type:
            values = self.get_enum_values(nested_enum)
            nested_enums.append(
                {
                    "name": nested_enum.name,
                    "full_name": f"{type_prefix}.{nested_enum.name}",
                    "values": values,
                }
            )

        # Рекурсивно обрабатываем вложенные перечисления в сообщениях
        for nested_message in message.nested_type:
            nested_enums.extend(self.get_nested_enums(nested_message, type_prefix))

        return nested_enums

    def get_package_name(self, proto_file: descriptor_pb2.FileDescriptorProto) -> str:
        """Get package name from proto file.

        Args:
            proto_file: Proto file descriptor

        Returns:
            Package name
        """
        return proto_file.package

    def get_imports(self, proto_file: descriptor_pb2.FileDescriptorProto) -> list[str]:
        """Get imports for the given proto file.

        Args:
            proto_file: Proto file descriptor

        Returns:
            List of imports
        """
        imports = []

        # Импортируем классы из основного файла pb2
        # Формируем полный путь к файлу для импорта
        file_path = proto_file.name.replace(".proto", "_pb2")
        # Если имя файла не содержит путь, то используем просто имя файла
        if "/" not in proto_file.name:
            import_path = f"{file_path}"
        else:
            import_path = f"{'.'.join(proto_file.name.split('/')[:-1])}.{file_path.split('/')[-1]}"

        # Собираем имена всех сообщений для импорта
        message_names = [message.name for message in proto_file.message_type]
        if message_names:
            imports.append(f"from {import_path} import {', '.join(message_names)}")

        # Add imports for dependencies
        dependency_modules = set()
        for dependency in proto_file.dependency:
            # Обрабатываем стандартные google protobuf зависимости
            if dependency.startswith("google/protobuf/"):
                # Извлекаем имя модуля из пути к файлу (например, 'empty' из 'google/protobuf/empty.proto')
                module_name = dependency.replace(".proto", "").split("/")[-1]
                dependency_modules.add(module_name)
                imports.append(f"from google.protobuf import {module_name}_pb2")
            else:
                # Для других зависимостей используем относительные импорты
                module_name = dependency.replace(".proto", "_pb2").split("/")[-1]
                imports.append(f"from . import {module_name}")

        return imports

    def get_services(self, proto_file: descriptor_pb2.FileDescriptorProto) -> list[dict]:
        """Get services from proto file.

        Args:
            proto_file: Proto file descriptor

        Returns:
            List of services
        """
        services = []
        for service in proto_file.service:
            methods = self.get_service_methods(service)

            services.append(
                {
                    "name": service.name,
                    "methods": methods,
                    "full_name": f"{proto_file.package}.{service.name}",
                }
            )

        return services

    def get_messages(self, proto_file: descriptor_pb2.FileDescriptorProto) -> list[dict]:
        """Get messages from proto file.

        Args:
            proto_file: Proto file descriptor

        Returns:
            List of messages
        """
        messages = []

        # Обрабатываем основные сообщения
        for message in proto_file.message_type:
            fields = self.get_message_fields(message)

            # Получаем вложенные типы и перечисления
            nested_types = self.get_nested_types(message)
            nested_enums = self.get_nested_enums(message)

            messages.append(
                {
                    "name": message.name,
                    "fields": fields,
                    "nested_types": nested_types,
                    "nested_enums": nested_enums,
                }
            )

        return messages

    def get_enums(self, proto_file: descriptor_pb2.FileDescriptorProto) -> list[dict]:
        """Get enums from proto file.

        Args:
            proto_file: Proto file descriptor

        Returns:
            List of enums
        """
        enums = []
        for enum in proto_file.enum_type:
            values = self.get_enum_values(enum)
            enums.append(
                {
                    "name": enum.name,
                    "values": values,
                }
            )

        return enums

    def get_output_filename(self, proto_file: descriptor_pb2.FileDescriptorProto, suffix: str = "_pb2_o3.py") -> str:
        """Get output filename for the given proto file.

        Args:
            proto_file: Proto file descriptor
            suffix: Suffix to append to the filename (default: _pb2_o3.py)

        Returns:
            Output filename
        """
        filename = proto_file.name.replace(".proto", suffix)
        return filename
