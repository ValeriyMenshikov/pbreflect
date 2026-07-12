"""Module for custom errors."""


class GenerationFailedError(Exception):
    """Raised when protoc fails to generate stubs."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class NoProtoFilesError(Exception):
    """Raised when no .proto files are found in the specified directory."""

    def __init__(self, proto_dir: str) -> None:
        super().__init__(f"No .proto files found in: {proto_dir}")
