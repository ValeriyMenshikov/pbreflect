"""Utilities for executing shell commands."""

from subprocess import CompletedProcess, run


class CommandExecutorImpl:
    """Implementation of command executor."""

    @staticmethod
    def execute(command: list[str]) -> tuple[int, str]:
        """Execute a command.

        Args:
            command: Command arguments as a list

        Returns:
            Tuple containing exit code and error output
        """
        result: CompletedProcess = run(
            args=command,
            capture_output=True,
            text=False,
            check=False,
        )

        # Handle potential encoding issues
        if result.stderr:
            try:
                stderr = result.stderr.decode("utf-8")
            except UnicodeDecodeError:
                stderr = result.stderr.decode("windows-1251")
        else:
            stderr = ""

        return result.returncode, stderr
