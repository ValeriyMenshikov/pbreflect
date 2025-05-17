"""Module with generators runner."""

import os
import shutil
from pathlib import Path
from typing import Literal

from pbreflect.pbgen.generators.base import BaseGenerator
from pbreflect.pbgen.generators.factory import GeneratorFactoryImpl
from pbreflect.pbgen.patchers.directory_structure_patcher import DirectoryStructurePatcher
from pbreflect.pbgen.patchers.import_patcher import ImportPatcher
from pbreflect.pbgen.patchers.mypy_patcher import MypyPatcher
from pbreflect.pbgen.patchers.patcher_protocol import CodePatcher
from pbreflect.pbgen.patchers.proto_import_patcher import ProtoImportPatcher
from pbreflect.pbgen.utils.command import CommandExecutorImpl
from pbreflect.pbgen.utils.file_finder import ProtoFileFinderImpl


def run(
    proto_dir: str,
    output_dir: str,
    gen_type: Literal["default", "mypy", "betterproto"] = "default",
    refresh: bool = False,
    root_path: Path | None = None,
) -> None:
    """Run generation of stubs.

    Args:
        proto_dir: Directory with proto files
        output_dir: Directory where to generate code
        gen_type: Type of generator to use
        refresh: Whether to refresh the output directory
        root_path: Root project directory
    """
    # Ensure proto directory exists
    if not os.path.exists(proto_dir):
        raise FileNotFoundError(f"Proto directory not found: {proto_dir}")

    # Refresh output directory if needed
    if refresh and os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    os.makedirs(output_dir, exist_ok=True)

    root_path = root_path or Path.cwd()

    # Patch proto files before generation
    proto_patcher = ProtoImportPatcher(proto_dir)
    proto_patcher.patch()

    # Create generator
    proto_finder = ProtoFileFinderImpl()
    command_executor = CommandExecutorImpl()
    generator_factory = GeneratorFactoryImpl()

    # Generate code
    generator = BaseGenerator(
        proto_finder=proto_finder,
        command_executor=command_executor,
        generator_factory=generator_factory,
    )
    generator.generate(
        proto_dir=proto_dir,
        output_dir=output_dir,
        gen_type=gen_type,
    )

    # Create patchers for generated code
    patchers: list[CodePatcher] = [
        DirectoryStructurePatcher(output_dir),
        ImportPatcher(output_dir, root_path),
    ]

    # Add mypy patcher if needed
    if gen_type == "mypy":
        patchers.append(MypyPatcher(output_dir))

    # Add proto import patcher
    patchers.append(ProtoImportPatcher(output_dir))

    # Apply all patchers
    for patcher in patchers:
        patcher.patch()
