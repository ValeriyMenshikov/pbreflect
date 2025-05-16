"""Implementation of proto import patcher."""

import re
import shutil
from keyword import kwlist
from pathlib import Path


class ProtoImportPatcher:
    """Patcher for import statements in proto files."""

    def __init__(self, proto_dir: str) -> None:
        """Initialize the import patcher.

        Args:
            proto_dir: Directory containing proto files
        """
        self.proto_dir = Path(proto_dir)

    def patch_imports(self) -> None:
        """Patch import statements in proto files."""
        self.patch_incorrect_local_imports()
        self.remove_gitlab_path()

    def patch_file_names(self) -> None:
        """Patch file names that might cause issues."""
        self.patch_keywords_in_file_names()
        
    def patch(self) -> None:
        """Apply all patches."""
        self.patch_imports()
        self.patch_file_names()

    def patch_incorrect_local_imports(self) -> None:
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
                                new_import = path.relative_to(
                                    self.proto_dir.absolute()
                                ).as_posix()
                                self._replace_import(imp, new_import, proto_path)
                        parent = parent.parent.absolute()

    def patch_keywords_in_file_names(self) -> None:
        """Patch proto files with Python keywords in their names."""
        for proto_path in self.proto_dir.rglob("*.proto"):
            if not proto_path.is_file():
                continue

            file_name = proto_path.stem
            if file_name in kwlist:
                new_file_name = f"{file_name}_.proto"
                new_path = proto_path.parent.joinpath(new_file_name)
                shutil.copy(proto_path, new_path)

    def remove_gitlab_path(self) -> None:
        """Remove GitLab-specific paths from import statements."""
        for proto_path in self.proto_dir.rglob("*.proto"):
            if not proto_path.is_file():
                continue

            imports = self._get_imports(proto_path)
            for imp in imports:
                if "/" in imp and not imp.startswith("google/"):
                    parts = imp.split("/")
                    if len(parts) > 2 and parts[0].startswith("gitlab"):
                        new_import = "/".join(parts[2:])
                        self._replace_import(imp, new_import, proto_path)

    @staticmethod
    def _replace_import(old_import: str, new_import: str, proto_path: Path) -> None:
        """Replace import statement in a proto file."""
        import_pattern = 'import "{}";'
        with open(proto_path, encoding="UTF-8") as proto:
            content = proto.read()
        with open(proto_path, "w", encoding="UTF-8") as proto:
            proto.write(
                content.replace(
                    import_pattern.format(old_import), import_pattern.format(new_import)
                )
            )

    @staticmethod
    def _get_imports(proto_path: Path) -> list[str]:
        """Get all import statements from a proto file."""
        imports = []
        with open(proto_path, encoding="UTF-8") as proto:
            for line in proto.readlines():
                if line.strip().startswith('import "'):
                    import_path = re.search(r'import "(.*?)";', line).group(1)
                    imports.append(import_path)
        return imports
