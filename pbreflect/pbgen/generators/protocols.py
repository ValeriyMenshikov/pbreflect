"""Protocols for code generation components."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class GeneratorStrategy(Protocol):
    """Provides the protoc command template for a specific output format."""

    @property
    def command_template(self) -> list[str]: ...


@runtime_checkable
class CommandExecutor(Protocol):
    """Executes shell commands and returns (exit_code, stderr)."""

    def execute(self, command: list[str]) -> tuple[int, str]: ...


@runtime_checkable
class ProtoFileFinder(Protocol):
    """Finds .proto files under a directory."""

    @property
    def proto_dir(self) -> str: ...

    def find_proto_files(self) -> list[str]: ...
