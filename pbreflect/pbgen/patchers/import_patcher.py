"""Implementation of import patcher for generated files."""

import re
from pathlib import Path


class ImportPatcher:
    """Patcher for import statements in generated code.

    This class implements the CodePatcher protocol.
    """

    def __init__(self, code_dir: str, root_path: Path) -> None:
        """Initialize the import patcher.

        Args:
            code_dir: Directory with generated code
            root_path: Root project directory
        """
        self.code_dir = Path(code_dir)
        self.root_path = root_path or Path.cwd()

    def patch(self) -> None:
        """Apply all patches."""
        self._patch_imports()

    def _patch_imports(self) -> None:
        """Fix import statements in generated code."""
        self._patch_python_imports()

    def _patch_python_imports(self) -> None:
        """Patch imports in Python stub files."""
        output_files = [str(p) for p in self.code_dir.rglob("*.py")]
        expected_root_path = str(
            self.code_dir.absolute().relative_to(self.root_path).as_posix()
        ).replace("/", ".")

        for f in output_files:
            imports = self._get_imports(Path(f))
            for imp in imports:
                if (
                    not imp.startswith(expected_root_path)
                    and not imp.startswith("google")
                    and not imp.endswith("._utilities")
                ):
                    new_imp = f"{expected_root_path}.{imp}"
                    self._replace_import(imp, new_imp, Path(f))

    @staticmethod
    def _replace_import(old_import: str, new_import: str, file_path: Path) -> None:
        """Replace import statement in a file."""
        with open(file_path, encoding="UTF-8") as file:
            content = file.read()
        with open(file_path, "w", encoding="UTF-8") as file:
            file.write(content.replace(f"from {old_import} import", f"from {new_import} import"))

    @staticmethod
    def _get_imports(file_path: Path) -> list[str]:
        """Get all import statements from a file."""
        imports = []
        with open(file_path, encoding="UTF-8") as proto:
            for line in proto.readlines():
                if line.strip().startswith("from "):
                    import_path = re.search(r"from(.*?)import", line).group(1).strip()
                    imports.append(import_path)
        return imports
