"""Base implementation of code generator."""

import logging
from pathlib import Path
from typing import Protocol

from pbreflect.pbgen.errors import GenerationFailedError, NoProtoFilesError


class BaseGenerator:
    """Base implementation of code generator."""

    def __init__(
        self,
        proto_finder,
        command_executor,
        generator_factory,
    ) -> None:
        """Initialize the base generator.

        Args:
            proto_finder: File finder for proto files
            command_executor: Command executor for running protoc
            generator_factory: Factory for creating generator strategies
        """
        self.proto_finder = proto_finder
        self.command_executor = command_executor
        self.generator_factory = generator_factory

        # Configure logging
        logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s")
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def _check_stubs_exists(self, proto_path: Path, include_dir: str, output_dir: str) -> bool:
        """Check if stubs are already generated for a proto file.

        Args:
            proto_path: Path to proto file
            include_dir: Directory with proto files
            output_dir: Directory where to generate stubs

        Returns:
            True if stubs exist, False otherwise
        """
        path_from_include = Path(proto_path).relative_to(Path(include_dir))
        patched_proto_path = Path(
            path_from_include.as_posix()
            .replace(".proto", "_pb2.py")
            .replace("-", "_")
            .replace(".", "/")
        )
        stubs_path = Path(output_dir).joinpath(patched_proto_path)
        return stubs_path.exists()

    def generate(self, proto_dir: str, output_dir: str, gen_type: str, root_path: Path) -> None:
        """Generate stubs for all proto files in the include directory.

        Args:
            proto_dir: Directory with proto files
            output_dir: Directory where to generate stubs
            gen_type: Type of generator to use
            root_path: Root project directory

        Raises:
            NoProtoFilesError: If no proto files are found
            GenerationFailedError: If generation fails for any proto file
        """
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Create generator strategy
        strategy = self.generator_factory.create_generator(gen_type, root_path)
        
        # Find proto files
        protos = self.proto_finder.find_proto_files(proto_dir)

        if not protos:
            raise NoProtoFilesError(proto_dir)

        self.logger.info("Starting generation python code...")
        for proto in protos:
            if self._check_stubs_exists(proto, proto_dir, output_dir):
                continue

            self.logger.info(f"Generating code for proto: {proto}...")
            command = strategy.command_template.format(
                include=proto_dir, output=output_dir, proto=proto
            )
            exit_code, stderr = self.command_executor.execute(command)

            if stderr.strip():
                for line in stderr.splitlines():
                    starts_with_path = line.split(":")[0].endswith(".proto")
                    if (
                        "warning: " not in line.lower()
                        and not line.startswith("Writing")
                        and starts_with_path
                    ):
                        self.logger.error(stderr)
                        raise GenerationFailedError

        self.logger.info("Generation completed!")
