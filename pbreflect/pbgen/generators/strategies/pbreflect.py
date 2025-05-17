"""PbReflect generator strategy."""

from pbreflect.pbgen.generators.protocols import GeneratorStrategy


class PbReflectGeneratorStrategy(GeneratorStrategy):
    """PbReflect generator strategy."""

    command_template = (
        "python -m grpc_tools.protoc "
        "--proto_path={include} "
        "--python_out={output} "
        "--mypy_out=readable_stubs,quiet:{output} "
        "--pbreflect_out={output} "
        "{proto}"
    )
