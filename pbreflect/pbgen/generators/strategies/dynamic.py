"""Dynamic generator strategy implementation."""

from pbreflect.pbgen.generators.protocols import GeneratorStrategy


class DynamicGeneratorStrategy(GeneratorStrategy):
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
        return f"python -m grpc_tools.protoc --proto_path={{include}} --{self.compiler}_out={{output}} {{proto}}"
