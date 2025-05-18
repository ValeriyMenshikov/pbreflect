import os

from pbreflect.pbgen.utils.command import CommandExecutorImpl


def format_file(target_dir: str, suffix: str | None = None) -> None:
    """Format generated code using ruff formatter and linter.

    Args:
        target_dir: Directory containing files to format
        suffix: Optional suffix to filter files (e.g., "_pbreflect.py")
    """
    executor = CommandExecutorImpl()

    if suffix:
        files_to_format = []
        for root, _, files in os.walk(target_dir):
            for file in files:
                if file.endswith(suffix):
                    files_to_format.append(os.path.join(root, file))

        if files_to_format:
            format_command = ["ruff", "format"] + files_to_format
            executor.execute(format_command)

            # Run linter with auto-fix
            lint_command = ["ruff", "check", "--fix"] + files_to_format
            executor.execute(lint_command)
    else:
        format_command = ["ruff", "format", target_dir]
        executor.execute(format_command)

        lint_command = ["ruff", "check", target_dir, "--fix"]
        executor.execute(lint_command)
