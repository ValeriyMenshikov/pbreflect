"""Utilities for executing shell commands."""

from subprocess import CompletedProcess, run


class CommandExecutor:
    """Runs a subprocess command and returns (exit_code, stderr)."""

    @staticmethod
    def execute(command: list[str]) -> tuple[int, str]:
        result: CompletedProcess = run(
            args=command,
            capture_output=True,
            text=False,
            check=False,
        )
        if result.stderr:
            try:
                stderr = result.stderr.decode("utf-8")
            except UnicodeDecodeError:
                stderr = result.stderr.decode("windows-1251")
        else:
            stderr = ""
        return result.returncode, stderr
