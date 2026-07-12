"""Tests for GenerationPipeline."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from pbreflect.pbgen.generators.factory import GeneratorType
from pbreflect.pbgen.runner import GenerationOptions, GenerationPipeline


class TestGenerationOptions:
    """Tests for GenerationOptions dataclass."""

    def test_defaults(self) -> None:
        opts = GenerationOptions()
        assert opts.gen_type == GeneratorType.PBREFLECT
        assert opts.refresh is False
        assert opts.async_mode is False
        assert opts.template_dir is None
        assert opts.gen_tests is False
        assert opts.tests_dir == "tests"
        assert opts.tests_template_dir is None
        assert opts.tests_client_module == "clients"

    def test_custom_values(self) -> None:
        opts = GenerationOptions(
            gen_type=GeneratorType.MYPY,
            refresh=True,
            async_mode=True,
            gen_tests=True,
            tests_dir="custom_tests",
            tests_template_dir="/custom/tmpl",
            tests_client_module="my_clients",
        )
        assert opts.gen_type == GeneratorType.MYPY
        assert opts.refresh is True
        assert opts.async_mode is True
        assert opts.gen_tests is True
        assert opts.tests_dir == "custom_tests"
        assert opts.tests_template_dir == "/custom/tmpl"
        assert opts.tests_client_module == "my_clients"


class TestGenerationPipelineRun:
    """Tests for GenerationPipeline.run."""

    @patch("pbreflect.pbgen.runner.os.makedirs")
    def test_run_calls_pipeline_stages(
        self,
        mock_makedirs: MagicMock,
        tmp_path: Path,
    ) -> None:
        with (
            patch("pbreflect.pbgen.runner.ProtoImportPatcher") as mock_import_patcher,
            patch("pbreflect.pbgen.runner.GeneratorFactory") as mock_factory_cls,
            patch("pbreflect.pbgen.runner.ClientGenerator") as mock_generator_cls,
            patch("pbreflect.pbgen.runner.ProtoFileFinder"),
            patch("pbreflect.pbgen.runner.CommandExecutor"),
            patch("pbreflect.pbgen.runner.DirectoryStructurePatcher") as mock_dir_patcher,
            patch("pbreflect.pbgen.runner.ImportPatcher") as mock_import_p,
            patch("pbreflect.pbgen.runner.MypyPatcher") as mock_mypy_p,
            patch("pbreflect.pbgen.runner.PbReflectPatcher") as mock_pb_p,
            patch("pbreflect.pbgen.runner.InitFilePatcher") as mock_init_p,
        ):
            mock_strategy = MagicMock()
            mock_factory_cls.return_value.create_generator.return_value = mock_strategy

            pipeline = GenerationPipeline(
                str(tmp_path / "protos"),
                str(tmp_path / "output"),
                GenerationOptions(),
            )
            pipeline.run()

            mock_import_patcher.return_value.patch.assert_called_once()
            mock_factory_cls.return_value.create_generator.assert_called_once()
            mock_generator_cls.return_value.generate.assert_called_once()
            for mock_p in [mock_dir_patcher, mock_import_p, mock_mypy_p, mock_pb_p, mock_init_p]:
                mock_p.return_value.patch.assert_called_once()
            mock_makedirs.assert_called()

    @patch("pbreflect.pbgen.runner.os.makedirs")
    @patch("pbreflect.pbgen.runner.shutil.rmtree")
    @patch("pbreflect.pbgen.runner.os.path.exists")
    def test_refresh_clears_output_dir(
        self,
        mock_exists: MagicMock,
        mock_rmtree: MagicMock,
        mock_makedirs: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_exists.return_value = True

        with (
            patch("pbreflect.pbgen.runner.ProtoImportPatcher"),
            patch("pbreflect.pbgen.runner.GeneratorFactory"),
            patch("pbreflect.pbgen.runner.ClientGenerator"),
            patch("pbreflect.pbgen.runner.ProtoFileFinder"),
            patch("pbreflect.pbgen.runner.CommandExecutor"),
            patch("pbreflect.pbgen.runner.DirectoryStructurePatcher"),
            patch("pbreflect.pbgen.runner.ImportPatcher"),
            patch("pbreflect.pbgen.runner.MypyPatcher"),
            patch("pbreflect.pbgen.runner.PbReflectPatcher"),
            patch("pbreflect.pbgen.runner.InitFilePatcher"),
        ):
            pipeline = GenerationPipeline(
                str(tmp_path / "protos"),
                str(tmp_path / "output"),
                GenerationOptions(refresh=True),
            )
            pipeline.run()

        mock_rmtree.assert_called_once()

    @patch("pbreflect.pbgen.runner.os.makedirs")
    @patch("pbreflect.pbgen.runner.shutil.rmtree")
    @patch("pbreflect.pbgen.runner.os.path.exists")
    def test_no_refresh_does_not_clear(
        self,
        mock_exists: MagicMock,
        mock_rmtree: MagicMock,
        mock_makedirs: MagicMock,
        tmp_path: Path,
    ) -> None:
        with (
            patch("pbreflect.pbgen.runner.ProtoImportPatcher"),
            patch("pbreflect.pbgen.runner.GeneratorFactory"),
            patch("pbreflect.pbgen.runner.ClientGenerator"),
            patch("pbreflect.pbgen.runner.ProtoFileFinder"),
            patch("pbreflect.pbgen.runner.CommandExecutor"),
            patch("pbreflect.pbgen.runner.DirectoryStructurePatcher"),
            patch("pbreflect.pbgen.runner.ImportPatcher"),
            patch("pbreflect.pbgen.runner.MypyPatcher"),
            patch("pbreflect.pbgen.runner.PbReflectPatcher"),
            patch("pbreflect.pbgen.runner.InitFilePatcher"),
        ):
            pipeline = GenerationPipeline(
                str(tmp_path / "protos"),
                str(tmp_path / "output"),
                GenerationOptions(refresh=False),
            )
            pipeline.run()

        mock_rmtree.assert_not_called()

    @patch("pbreflect.pbgen.runner.os.makedirs")
    def test_gen_tests_triggers_test_generation(
        self,
        mock_makedirs: MagicMock,
        tmp_path: Path,
    ) -> None:
        with (
            patch("pbreflect.pbgen.runner.ProtoImportPatcher"),
            patch("pbreflect.pbgen.runner.GeneratorFactory"),
            patch("pbreflect.pbgen.runner.ClientGenerator"),
            patch("pbreflect.pbgen.runner.ProtoFileFinder"),
            patch("pbreflect.pbgen.runner.CommandExecutor"),
            patch("pbreflect.pbgen.runner.DirectoryStructurePatcher"),
            patch("pbreflect.pbgen.runner.ImportPatcher"),
            patch("pbreflect.pbgen.runner.MypyPatcher"),
            patch("pbreflect.pbgen.runner.PbReflectPatcher"),
            patch("pbreflect.pbgen.runner.InitFilePatcher"),
            patch("pbreflect.pbgen.plugins.tests.runner.run_test_generation") as mock_test_gen,
        ):
            pipeline = GenerationPipeline(
                str(tmp_path / "protos"),
                str(tmp_path / "output"),
                GenerationOptions(gen_tests=True, tests_dir="my_tests", tests_template_dir="/custom/tmpl"),
            )
            pipeline.run()

        mock_test_gen.assert_called_once()
        call_kwargs = mock_test_gen.call_args.kwargs
        assert call_kwargs["tests_output_dir"] == "my_tests"
        assert call_kwargs["template_dir"] == "/custom/tmpl"

    @patch("pbreflect.pbgen.runner.os.makedirs")
    def test_no_gen_tests_skips_test_generation(
        self,
        mock_makedirs: MagicMock,
        tmp_path: Path,
    ) -> None:
        with (
            patch("pbreflect.pbgen.runner.ProtoImportPatcher"),
            patch("pbreflect.pbgen.runner.GeneratorFactory"),
            patch("pbreflect.pbgen.runner.ClientGenerator"),
            patch("pbreflect.pbgen.runner.ProtoFileFinder"),
            patch("pbreflect.pbgen.runner.CommandExecutor"),
            patch("pbreflect.pbgen.runner.DirectoryStructurePatcher"),
            patch("pbreflect.pbgen.runner.ImportPatcher"),
            patch("pbreflect.pbgen.runner.MypyPatcher"),
            patch("pbreflect.pbgen.runner.PbReflectPatcher"),
            patch("pbreflect.pbgen.runner.InitFilePatcher"),
            patch("pbreflect.pbgen.plugins.tests.runner.run_test_generation") as mock_test_gen,
        ):
            pipeline = GenerationPipeline(
                str(tmp_path / "protos"),
                str(tmp_path / "output"),
                GenerationOptions(gen_tests=False),
            )
            pipeline.run()

        mock_test_gen.assert_not_called()
