"""Default generator strategy implementation."""

from pathlib import Path


class DefaultGeneratorStrategy:
    """Strategy for standard protobuf Python stub generation."""

    @property
    def command_template(self) -> str:
        """Command template for this generator.

        Returns:
            Command template string
        """
        return (
            "python -m grpc.tools.protoc -I {include}"
            " --python_out={output} --grpc_python_out={output} {proto}"
        )
