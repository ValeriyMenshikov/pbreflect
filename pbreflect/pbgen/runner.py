"""Runner for code generation."""

import os
import shutil
from pathlib import Path
from typing import Literal, List

from pbreflect.pbgen.generators.factory import GeneratorFactoryImpl
from pbreflect.pbgen.generators.protocols import GeneratorStrategy
from pbreflect.pbgen.patchers.directory_structure_patcher import DirectoryStructurePatcher
from pbreflect.pbgen.patchers.import_patcher import ImportPatcher
from pbreflect.pbgen.patchers.mypy_patcher import MypyPatcher
from pbreflect.pbgen.patchers.pbreflect_patcher import PbReflectPatcher
from pbreflect.pbgen.patchers.proto_import_patcher import ProtoImportPatcher
from pbreflect.pbgen.utils.command import CommandExecutorImpl
from pbreflect.pbgen.utils.file_finder import ProtoFileFinderImpl


def run(
    proto_dir: str,
    output_dir: str,
    gen_type: Literal["default", "mypy", "betterproto", "pbreflect"],
    refresh: bool = False,
    root_path: Path | None = None,
) -> None:
    """Run code generation.

    Args:
        proto_dir: Directory with proto files
        output_dir: Directory where to generate code
        gen_type: Type of generator
        refresh: Whether to refresh the output directory
        root_path: Root project directory
    """
    if refresh and os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Use current directory as root path if not specified
    root_path = root_path or Path.cwd()

    # Patch proto files before generation
    proto_patchers = [
        ProtoImportPatcher(proto_dir),
    ]

    for patcher in proto_patchers:
        patcher.patch()

    # Generate code
    proto_finder = ProtoFileFinderImpl(proto_dir)
    command_executor = CommandExecutorImpl()
    generator_factory = GeneratorFactoryImpl()

    # Create generator based on type
    generator_strategy = generator_factory.create_generator(gen_type)

    # Generate code
    from pbreflect.pbgen.generators.base import BaseGenerator

    generator = BaseGenerator(proto_finder, command_executor, generator_factory)
    generator.generate(output_dir, generator_strategy)

    # Patch generated code
    patchers = [
        DirectoryStructurePatcher(output_dir),
        ImportPatcher(output_dir, root_path),
    ]

    # Add specific patchers based on generator type
    if gen_type == "mypy":
        patchers.append(MypyPatcher(output_dir))
    elif gen_type == "pbreflect":
        patchers.append(PbReflectPatcher(output_dir))

    # Apply all patchers
    for patcher in patchers:
        patcher.patch()
