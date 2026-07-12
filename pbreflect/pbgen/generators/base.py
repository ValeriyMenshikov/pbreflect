"""Code generator that drives protoc via a pluggable strategy."""

from pathlib import Path

from pbreflect.log import get_logger
from pbreflect.pbgen.errors import GenerationFailedError, NoProtoFilesError
from pbreflect.pbgen.generators.protocols import CommandExecutor, GeneratorStrategy, ProtoFileFinder

_logger = get_logger(__name__)


class ClientGenerator:
    """Runs protoc for every .proto file found by the finder, using the given strategy."""

    def __init__(self, proto_finder: ProtoFileFinder, command_executor: CommandExecutor) -> None:
        self._finder = proto_finder
        self._executor = command_executor

    def generate(self, output_dir: str, strategy: GeneratorStrategy) -> None:
        _logger.info("Starting code generation…")
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        proto_files = self._finder.find_proto_files()
        if not proto_files:
            raise NoProtoFilesError(self._finder.proto_dir)

        for proto_file in proto_files:
            _logger.info("Generating code for proto: %s", proto_file)
            command_args = [
                arg.format(include=self._finder.proto_dir, output=output_dir, proto=proto_file)
                for arg in strategy.command_template
            ]
            exit_code, stderr = self._executor.execute(command_args)
            if exit_code != 0:
                msg = f"protoc failed for {proto_file}: {stderr}"
                _logger.error(msg)
                raise GenerationFailedError(msg)

        _logger.info("Code generation completed.")
