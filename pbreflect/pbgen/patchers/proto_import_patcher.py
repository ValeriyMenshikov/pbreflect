"""Implementation of proto import patcher."""

import re
import shutil
from keyword import kwlist
from pathlib import Path


class ProtoImportPatcher:
    """Patcher for import statements in proto files.

    This class implements the CodePatcher protocol.
    """

    def __init__(self, proto_dir: str) -> None:
        """Initialize the import patcher.

        Args:
            proto_dir: Directory containing proto files
        """
        self.proto_dir = Path(proto_dir)

    def patch(self) -> None:
        """Apply all patches."""
        self._patch_imports()
        self._patch_file_names()

    def _patch_imports(self) -> None:
        """Patch import statements in proto files."""
        self._patch_incorrect_local_imports()
        self._remove_gitlab_path()

    def _patch_file_names(self) -> None:
        """Patch file names that might cause issues."""
        self._patch_keywords_in_file_names()

    def _patch_incorrect_local_imports(self) -> None:
        """Patch local imports that are referenced from the root directory."""
        for proto_path in self.proto_dir.rglob("*.proto"):
            if not proto_path.is_file():
                continue

            imports = self._get_imports(proto_path)
            for imp in imports:
                normal_path = self.proto_dir.joinpath(Path(imp))
                if not normal_path.exists():
                    parent = proto_path.parent.absolute()
                    while parent.absolute() != self.proto_dir.absolute():
                        for path in parent.rglob("*.proto"):
                            if imp in path.as_posix():
                                new_import = path.relative_to(self.proto_dir.absolute()).as_posix()
                                self._replace_import(imp, new_import, proto_path)
                        parent = parent.parent

    def _remove_gitlab_path(self) -> None:
        """Remove gitlab path from import statements."""
        for proto_path in self.proto_dir.rglob("*.proto"):
            if not proto_path.is_file():
                continue

            imports = self._get_imports(proto_path)
            for imp in imports:
                if "gitlab" in imp:
                    new_import = imp.split("/")[-1]
                    self._replace_import(imp, new_import, proto_path)

    def _patch_keywords_in_file_names(self) -> None:
        """Patch file names that use Python keywords."""
        for proto_path in self.proto_dir.rglob("*.proto"):
            if not proto_path.is_file():
                continue

            filename = proto_path.stem
            if filename in kwlist:
                new_path = proto_path.with_stem(f"{filename}_pb")
                shutil.copy(proto_path, new_path)

    @staticmethod
    def _replace_import(old_import: str, new_import: str, file_path: Path) -> None:
        """Replace import statement in proto file."""
        with open(file_path, encoding="UTF-8") as file:
            content = file.read()
        with open(file_path, "w", encoding="UTF-8") as file:
            file.write(content.replace(f'import "{old_import}"', f'import "{new_import}"'))

    @staticmethod
    def _get_imports(file_path: Path) -> list[str]:
        """Get all import statements from proto file."""
        imports = []
        with open(file_path, encoding="UTF-8") as proto:
            for line in proto.readlines():
                if line.strip().startswith("import "):
                    match = re.search(r'"(.*?)"', line)
                    if match:
                        import_path = match.group(1)
                        imports.append(import_path)
        return imports
