"""Implementation of directory structure patcher for generated files."""

import shutil
from pathlib import Path


class DirectoryStructurePatcher:
    """Patcher for directory structure issues in generated code."""

    def __init__(self, code_dir: str) -> None:
        """Initialize the directory structure patcher.

        Args:
            code_dir: Directory with generated code
        """
        self.code_dir = Path(code_dir)

    def patch_directory_structure(self) -> None:
        """Fix directory structure issues in generated code."""
        self.move_dirs_with_dots()

    def patch(self) -> None:
        """Apply all patches."""
        self.patch_directory_structure()

    def move_dirs_with_dots(self) -> None:
        """Move files from incorrectly generated directories."""
        for path in self.code_dir.rglob("*"):
            if path.is_dir() and "." in path.name:
                for file in path.rglob("*_pb2_*"):
                    old_folder = file.parent.relative_to(self.code_dir).as_posix()
                    new_path = Path(self.code_dir, old_folder.replace(".", "/")).joinpath(
                        file.name
                    )
                    new_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(file.as_posix(), new_path)
                shutil.rmtree(str(path))
