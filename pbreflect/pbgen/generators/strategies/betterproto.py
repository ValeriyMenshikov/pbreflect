"""BetterProto generator strategy implementation."""

from pathlib import Path


class BetterProtoGeneratorStrategy:
    """Strategy for betterproto stub generation."""

    @property
    def command_template(self) -> str:
        """Command template for this generator.

        Returns:
            Command template string
        """
        return "python -m grpc.tools.protoc -I {include} --python_betterproto_out={output} {proto}"
