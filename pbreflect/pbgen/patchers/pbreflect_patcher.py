"""Patcher for PbReflect generated code."""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Protocol, Set


class CodePatcher(Protocol):
    """Protocol for code patchers."""

    def patch(self) -> None:
        """Patch the code."""
        ...


class PbReflectPatcher:
    """Patcher for PbReflect generated code."""

    def __init__(self, output_dir: str) -> None:
        """Initialize the patcher.

        Args:
            output_dir: Directory with generated code
        """
        self.output_dir = output_dir

    def patch(self) -> None:
        """Patch the generated code.

        This method walks through the output directory and fixes imports in the
        generated _pb2_o3.py files.
        """
        for root, _, files in os.walk(self.output_dir):
            for file in files:
                if file.endswith("_pb2_o3.py"):
                    self._patch_file(os.path.join(root, file))

    def _extract_message_types(self, content: str) -> Set[str]:
        """Extract message types from the file content.

        Args:
            content: File content

        Returns:
            Set of message type names
        """
        # Ищем все типы в кавычках
        types = set()

        # Ищем типы в аннотациях параметров и возвращаемых значений
        param_types = re.findall(r'request: "([^"]+)"', content)
        return_types = re.findall(r'\) -> "([^"]+)"', content)

        # Добавляем все найденные типы
        types.update(param_types)
        types.update(return_types)

        # Отдельно обрабатываем типы списков
        list_types = re.findall(r'\) -> "List\[([^]]+)\]"', content)
        types.update(list_types)

        return types

    def _patch_file(self, file_path: str) -> None:
        """Patch a single file.

        Args:
            file_path: Path to the file to patch
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Исправляем импорты стандартных модулей Python
        content = re.sub(
            r"from pb\.typing import",
            "from typing import",
            content,
        )
        content = re.sub(
            r"from pb\.abc import",
            "from abc import",
            content,
        )
        content = re.sub(
            r"from pb\.nuke\.grpc_client",
            "from nuke.grpc_client",
            content,
        )

        # Добавляем импорт cast, если его нет
        if "cast(" in content and "from typing import cast" not in content and "import cast" not in content:
            content = re.sub(
                r"from typing import ([^,]+)",
                r"from typing import cast, \1",
                content,
            )

        # Полностью заменяем импорт типов, чтобы избежать дублирования
        content = re.sub(
            r"from [\w\.]+ import Dict, List, Optional.*",
            "from typing import Dict, List, Optional, Union, Any, Callable, ClassVar, Type, cast",
            content,
        )

        # Исправляем импорты google protobuf
        content = re.sub(
            r"import google\.protobuf\.(\w+)_pb2",
            r"from google.protobuf import \1_pb2",
            content,
        )

        # Обрабатываем все импорты, чтобы избежать дублирования
        lines = content.split("\n")
        imports = []
        non_imports = []
        import_modules = {}  # модуль -> список импортов

        for line in lines:
            if line.startswith("from ") and " import " in line:
                # Извлекаем модуль и импорты
                module = line.split("from ")[1].split(" import ")[0]
                imports_str = line.split(" import ")[1]

                # Добавляем импорты в словарь
                if module not in import_modules:
                    import_modules[module] = []

                # Разбиваем строку импортов на отдельные элементы
                for imp in imports_str.split(", "):
                    if imp not in import_modules[module]:
                        import_modules[module].append(imp)
            else:
                non_imports.append(line)

        # Формируем новые строки импортов
        for module, imports_list in import_modules.items():
            imports.append(f"from {module} import {', '.join(imports_list)}")

        # Собираем файл заново
        # Находим индекс первой строки, которая не является импортом или пустой строкой
        first_non_import_index = 0
        for i, line in enumerate(non_imports):
            if line and not line.startswith("#") and not line.startswith('"""'):
                first_non_import_index = i
                break

        # Вставляем импорты перед первой непустой строкой, которая не является комментарием
        new_content = "\n".join(non_imports[:first_non_import_index] + imports + non_imports[first_non_import_index:])

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
