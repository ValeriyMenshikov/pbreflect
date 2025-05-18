"""PbReflect generator strategy."""

from pbreflect.pbgen.generators.protocols import GeneratorStrategy


class PbReflectGeneratorStrategy(GeneratorStrategy):
    """PbReflect generator strategy."""

    def __init__(self, async_mode: bool = True) -> None:
        """Initialize the PbReflect generator strategy.

        Args:
            async_mode: Whether to generate async client code (True) or sync client code (False)
        """
        self.async_mode = async_mode

    @property
    def command_template(self) -> str:
        """Get the command template for code generation.

        Returns:
            Command template string
        """
        plugin_options = []

        if not self.async_mode:
            plugin_options.append("async=false")

        plugin_params = ",".join(plugin_options)
        plugin_out = f"--pbreflect_out={plugin_params}:" + "{output}" if plugin_params else "--pbreflect_out={output}"

        return (
            "python -m grpc_tools.protoc "
            "--proto_path={include} "
            "--python_out={output} "
            "--mypy_out=readable_stubs,quiet:{output} "
            f"{plugin_out} "
            "{proto}"
        )
