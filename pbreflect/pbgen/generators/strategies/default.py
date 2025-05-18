"""Default generator strategy implementation."""


class DefaultGeneratorStrategy:
    """Strategy for standard protobuf Python stub generation."""

    @property
    def command_template(self) -> list[str]:
        """Command template for this generator.

        Returns:
            Command template as a list of arguments
        """
        return [
            "python",
            "-m",
            "grpc.tools.protoc",
            "-I",
            "{include}",
            "--python_out={output}",
            "--grpc_python_out={output}",
            "{proto}",
        ]
