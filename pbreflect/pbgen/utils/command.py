"""Utilities for executing shell commands."""

from subprocess import PIPE, Popen


class CommandExecutorImpl:
    """Implementation of command executor."""

    def execute(self, command: str) -> tuple[int, str]:
        """Execute a shell command.

        Args:
            command: Command to execute

        Returns:
            Tuple containing exit code and error output
        """
        process = Popen(command, shell=True, stderr=PIPE)
        process.wait()

        # Handle potential encoding issues
        try:
            stderr = process.stderr.read().decode("utf-8")
        except UnicodeDecodeError:
            stderr = process.stderr.read().decode("windows-1251")

        process.communicate()
        return process.returncode, stderr
