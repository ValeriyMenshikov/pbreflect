"""Mypy generator strategy implementation."""


class MyPyGeneratorStrategy:
    """Strategy for protobuf Python stub generation with mypy type interfaces."""

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
            "--mypy_out=readable_stubs,quiet:{output}",
            "--mypy_grpc_out=readable_stubs,quiet:{output}",
            "--python_out={output}",
            "--grpc_python_out={output}",
            "{proto}",
        ]
