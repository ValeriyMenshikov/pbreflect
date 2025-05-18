"""BetterProto generator strategy implementation."""


class BetterProtoGeneratorStrategy:
    """Strategy for betterproto stub generation."""

    @property
    def command_template(self) -> list[str]:
        """Command template for this generator.

        Returns:
            Command template as a list of arguments
        """
        return ["python", "-m", "grpc.tools.protoc", "-I", "{include}", "--python_betterproto_out={output}", "{proto}"]
