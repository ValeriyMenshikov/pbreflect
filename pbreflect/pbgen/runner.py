"""Runner for code generation.

This module provides the main entry point for generating client code from proto files.
It orchestrates the process of finding proto files, patching them if needed,
generating code using the appropriate generator, and applying post-generation patches.
"""

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
from pbreflect.pbgen.patchers.pb_reflect_patcher import PbReflectPatcher
from pbreflect.pbgen.patchers.proto_import_patcher import ProtoImportPatcher
from pbreflect.pbgen.utils.command import CommandExecutorImpl
from pbreflect.pbgen.utils.file_finder import ProtoFileFinderImpl


def run(
    proto_dir: str,
    output_dir: str,
    gen_type: Literal["default", "mypy", "betterproto", "pbreflect"],
    refresh: bool = False,
    root_path: Path | None = None,
    async_mode: bool = True,
) -> None:
    """Run code generation for proto files.

    This function orchestrates the entire code generation process:
    1. Optionally cleans the output directory
    2. Applies pre-generation patches to proto files
    3. Finds all proto files in the specified directory
    4. Generates code using the selected generator type
    5. Applies post-generation patches to the generated code

    Args:
        proto_dir: Directory containing proto files to process
        output_dir: Directory where generated code will be placed
        gen_type: Type of generator to use:
            - "default": Standard protoc Python output
            - "mypy": Standard output with mypy type annotations
            - "betterproto": Uses betterproto generator
            - "pbreflect": Custom generator with enhanced gRPC client support
        refresh: If True, clears the output directory before generation
        root_path: Root project directory, defaults to current working directory
        async_mode: Whether to generate async client code (True) or sync client code (False)
    """
    if refresh and os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    os.makedirs(output_dir, exist_ok=True)

    root_path = root_path or Path.cwd()

    proto_patchers: list[CodePatcher] = [
        ProtoImportPatcher(proto_dir),
    ]

    for patcher in proto_patchers:
        patcher.patch()

    proto_finder = ProtoFileFinderImpl(proto_dir)

    command_executor = CommandExecutorImpl()
    generator_factory = GeneratorFactoryImpl()

    generator_strategy = generator_factory.create_generator(
        gen_type,
        async_mode=async_mode,
    )

    generator = BaseGenerator(proto_finder, command_executor, generator_factory)
    generator.generate(output_dir, generator_strategy)

    # Patch generated code
    patchers: list[CodePatcher] = [
        DirectoryStructurePatcher(output_dir),
        ImportPatcher(output_dir, root_path),
        MypyPatcher(output_dir),
        PbReflectPatcher(output_dir),
    ]

    # Apply all patchers
    for patcher in patchers:
        patcher.patch()
