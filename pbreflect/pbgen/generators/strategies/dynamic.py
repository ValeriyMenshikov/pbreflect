"""Dynamic generator strategy implementation."""

from pathlib import Path


class DynamicGeneratorStrategy:
    """Strategy for using a dynamically specified compiler."""

    def __init__(self, compiler: str) -> None:
        """Initialize the dynamic generator strategy.

        Args:
            compiler: Name of the compiler plugin to use
        """
        self.compiler = compiler

    @property
    def command_template(self) -> str:
        """Command template for this generator.

        Returns:
            Command template string
        """
        return (
            "python -m grpc.tools.protoc -I {include}"
            f" --python_{self.compiler}_out"
            "={output} {proto}"
        )
