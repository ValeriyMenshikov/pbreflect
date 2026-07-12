import os

from pbreflect.pbgen.utils.command import CommandExecutor


def format_file(target_dir: str, suffix: str | None = None) -> None:
    """Format generated code using ruff formatter and linter."""
    executor = CommandExecutor()

    if suffix:
        files_to_format = [
            os.path.join(root, f)
            for root, _, files in os.walk(target_dir)
            for f in files
            if f.endswith(suffix)
        ]
        if files_to_format:
            executor.execute(["ruff", "format"] + files_to_format)
            executor.execute(["ruff", "check", "--fix"] + files_to_format)
    else:
        executor.execute(["ruff", "format", target_dir])
        executor.execute(["ruff", "check", target_dir, "--fix"])
