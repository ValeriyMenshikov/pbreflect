"""Implementation of mypy patcher for generated files."""

from pathlib import Path


class MypyPatcher:
    """Patcher for mypy interface files.

    This class implements the CodePatcher protocol.
    """

    def __init__(self, code_dir: str) -> None:
        """Initialize the mypy patcher.

        Args:
            code_dir: Directory with generated code
        """
        self.code_dir = Path(code_dir)

    def patch(self) -> None:
        """Apply all patches."""
        self._patch_imports()
        self._patch_type_annotations()

    def _patch_imports(self) -> None:
        """Fix import statements in mypy interface files."""
        self._patch_mypy_imports()

    def _patch_type_annotations(self) -> None:
        """Fix type annotations in mypy interface files."""
        # Currently handled as part of _patch_mypy_imports
        pass

    def _patch_mypy_imports(self) -> None:
        """Fix incorrect imports and class references in mypy interface files."""
        stubs = [str(p) for p in Path(self.code_dir).rglob("*.pyi")]
        # Get the output directory name from the path
        output_dir_name = Path(self.code_dir).name

        for stub in stubs:
            with open(stub, encoding="utf-8", errors="ignore") as sf:
                lines = sf.readlines()

            # Remove @final decorators and process imports
            i = 0
            while i < len(lines):
                line = lines[i]
                # Remove @final decorators
                if line.strip() == "@final":
                    lines.pop(i)
                    continue

                # Fix broken classes - check for specific patterns
                if "_EnumTypeWrapper" in line:
                    line = line.replace("_EnumTypeWrapper", "EnumTypeWrapper")
                    lines[i] = line
                elif "_ExtensionFieldDescriptor" in line:
                    line = line.replace("_ExtensionFieldDescriptor", "ExtensionFieldDescriptor")
                    lines[i] = line

                # Add type annotations for classes
                if line.startswith("class") and stub.endswith("_pb2.pyi"):
                    class_name = line.split("class ")[1].split("(")[0].split(":")[0]
                    lines.insert(i, f"\n{class_name}: {class_name}\n\n")
                    i += 2  # Skip the two lines we just inserted

                # Fix imports
                if "from " in line and " import" in line:
                    imp_str = line.split("from ")[1].split(" import")[0]
                    # Skip if it's a standard library import
                    if imp_str.startswith("google.") or imp_str.startswith("grpc."):
                        i += 1
                        continue

                    # Ensure the import path starts with the output directory name
                    if not imp_str.startswith(f"{output_dir_name}."):
                        # Check if this is a path within our output directory
                        relative_path = imp_str.replace(".", "/")
                        pb_path = Path(self.code_dir, f"{relative_path}.pyi")

                        if pb_path.exists():
                            # Add the output directory prefix to the import
                            new_imp = f"{output_dir_name}.{imp_str}"
                            line = line.replace(f"from {imp_str} import", f"from {new_imp} import")
                            lines[i] = line

                i += 1

            with open(stub, "w") as sf:
                sf.write("".join(lines))
