"""Code generation pipeline — orchestrates proto patching, client generation, and test stubs."""

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from pbreflect.pbgen.generators.base import ClientGenerator
from pbreflect.pbgen.generators.factory import GeneratorFactory, GeneratorType
from pbreflect.pbgen.patchers.directory_structure_patcher import DirectoryStructurePatcher
from pbreflect.pbgen.patchers.import_patcher import ImportPatcher
from pbreflect.pbgen.patchers.init_file_patcher import InitFilePatcher
from pbreflect.pbgen.patchers.mypy_patcher import MypyPatcher
from pbreflect.pbgen.patchers.patcher_protocol import CodePatcher
from pbreflect.pbgen.patchers.pb_reflect_patcher import PbReflectPatcher
from pbreflect.pbgen.patchers.proto_import_patcher import ProtoImportPatcher
from pbreflect.pbgen.utils.command import CommandExecutor
from pbreflect.pbgen.utils.file_finder import ProtoFileFinder


@dataclass
class GenerationOptions:
    """All tuneable knobs for a single generation run."""

    gen_type: GeneratorType = GeneratorType.PBREFLECT
    refresh: bool = False
    async_mode: bool = False
    template_dir: str | None = None
    gen_tests: bool = False
    tests_dir: str = "tests"
    tests_client_module: str = "clients"
    root_path: Path = field(default_factory=Path.cwd)


class GenerationPipeline:
    """Orchestrates the full client-code generation pipeline."""

    def __init__(self, proto_dir: str, output_dir: str, options: GenerationOptions | None = None) -> None:
        self._proto_dir = proto_dir
        self._output_dir = output_dir
        self._opts = options or GenerationOptions()

    def run(self) -> None:
        self._prepare_output_dir()
        self._patch_protos()
        self._generate_clients()
        self._patch_clients()
        if self._opts.gen_tests:
            self._generate_tests()

    def _prepare_output_dir(self) -> None:
        if self._opts.refresh and os.path.exists(self._output_dir):
            shutil.rmtree(self._output_dir)
        os.makedirs(self._output_dir, exist_ok=True)

    def _patch_protos(self) -> None:
        ProtoImportPatcher(self._proto_dir).patch()

    def _generate_clients(self) -> None:
        strategy = GeneratorFactory().create_generator(
            self._opts.gen_type,
            async_mode=self._opts.async_mode,
            template_dir=self._opts.template_dir,
        )
        ClientGenerator(ProtoFileFinder(self._proto_dir), CommandExecutor()).generate(self._output_dir, strategy)

    def _patch_clients(self) -> None:
        for patcher in self._client_patchers():
            patcher.patch()

    def _client_patchers(self) -> list[CodePatcher]:
        return [
            DirectoryStructurePatcher(self._output_dir),
            ImportPatcher(self._output_dir, self._opts.root_path),
            MypyPatcher(self._output_dir),
            PbReflectPatcher(self._output_dir),
            InitFilePatcher(self._output_dir),
        ]

    def _generate_tests(self) -> None:
        from pbreflect.pbgen.plugins.tests.runner import run_test_generation

        run_test_generation(
            proto_dir=self._proto_dir,
            tests_output_dir=self._opts.tests_dir,
            client_module=self._opts.tests_client_module,
            async_mode=self._opts.async_mode,
            template_dir=self._opts.template_dir,
        )
