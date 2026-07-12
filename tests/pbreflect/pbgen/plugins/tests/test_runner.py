"""Tests for run_test_generation."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from pbreflect.pbgen.plugins.tests.runner import run_test_generation


class TestRunTestGeneration:
    """Tests for run_test_generation."""

    @patch("pbreflect.pbgen.plugins.tests.runner.ProtoFileFinder")
    @patch("pbreflect.pbgen.plugins.tests.runner.os.makedirs")
    def test_no_proto_files_skips_generation(
        self,
        mock_makedirs: MagicMock,
        mock_finder_cls: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_finder_cls.return_value.find_proto_files.return_value = []

        run_test_generation(
            proto_dir=str(tmp_path / "protos"),
            tests_output_dir=str(tmp_path / "tests"),
        )

        mock_makedirs.assert_called_once()

    @patch("pbreflect.pbgen.plugins.tests.runner.protoc")
    @patch("pbreflect.pbgen.plugins.tests.runner.ProtoFileFinder")
    @patch("pbreflect.pbgen.plugins.tests.runner.os.makedirs")
    def test_protoc_failure_skips_generation(
        self,
        mock_makedirs: MagicMock,
        mock_finder_cls: MagicMock,
        mock_protoc: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_finder_cls.return_value.find_proto_files.return_value = ["a.proto"]
        mock_protoc.main.return_value = 1

        run_test_generation(
            proto_dir=str(tmp_path / "protos"),
            tests_output_dir=str(tmp_path / "tests"),
        )

        mock_makedirs.assert_called_once()

    @patch("pbreflect.pbgen.plugins.tests.runner.PbReflectTestsPlugin")
    @patch("pbreflect.pbgen.plugins.tests.runner.protoc")
    @patch("pbreflect.pbgen.plugins.tests.runner.ProtoFileFinder")
    @patch("pbreflect.pbgen.plugins.tests.runner.os.makedirs")
    def test_writes_generated_files(
        self,
        mock_makedirs: MagicMock,
        mock_finder_cls: MagicMock,
        mock_protoc: MagicMock,
        mock_plugin_cls: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_finder_cls.return_value.find_proto_files.return_value = ["test.proto"]

        import tempfile

        desc_file = tempfile.NamedTemporaryFile(suffix=".pb", delete=False)
        desc_file.write(b"")
        desc_file.close()

        mock_protoc.main.return_value = 0

        from google.protobuf.compiler import plugin_pb2

        response = plugin_pb2.CodeGeneratorResponse()
        out_file = response.file.add()
        out_file.name = "test_generated.py"
        out_file.content = "# test"

        mock_plugin_cls.return_value.process_request.return_value = response

        with (
            patch("pbreflect.pbgen.plugins.tests.runner.open") as mock_open,
            patch("pbreflect.pbgen.plugins.tests.runner.os.unlink"),
            patch("pbreflect.pbgen.plugins.tests.runner.os.path.exists", return_value=True),
        ):
            mock_open.side_effect = [
                open(desc_file.name, "rb"),
                MagicMock(),
            ]

            run_test_generation(
                proto_dir=str(tmp_path / "protos"),
                tests_output_dir=str(tmp_path / "tests"),
            )

        mock_plugin_cls.return_value.process_request.assert_called_once()

    @patch("pbreflect.pbgen.plugins.tests.runner.PbReflectTestsPlugin")
    @patch("pbreflect.pbgen.plugins.tests.runner.protoc")
    @patch("pbreflect.pbgen.plugins.tests.runner.ProtoFileFinder")
    @patch("pbreflect.pbgen.plugins.tests.runner.os.makedirs")
    def test_passes_template_dir_to_plugin(
        self,
        mock_makedirs: MagicMock,
        mock_finder_cls: MagicMock,
        mock_protoc: MagicMock,
        mock_plugin_cls: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_finder_cls.return_value.find_proto_files.return_value = ["test.proto"]
        mock_protoc.main.return_value = 0

        import tempfile

        desc_file = tempfile.NamedTemporaryFile(suffix=".pb", delete=False)
        desc_file.write(b"")
        desc_file.close()

        from google.protobuf.compiler import plugin_pb2

        response = plugin_pb2.CodeGeneratorResponse()
        mock_plugin_cls.return_value.process_request.return_value = response

        with (
            patch("pbreflect.pbgen.plugins.tests.runner.open") as mock_open,
            patch("pbreflect.pbgen.plugins.tests.runner.os.unlink"),
            patch("pbreflect.pbgen.plugins.tests.runner.os.path.exists", return_value=True),
        ):
            mock_open.side_effect = [
                open(desc_file.name, "rb"),
                MagicMock(),
            ]

            run_test_generation(
                proto_dir=str(tmp_path / "protos"),
                tests_output_dir=str(tmp_path / "tests"),
                template_dir="/custom/tmpl",
            )

        mock_plugin_cls.assert_called_once_with(template_dir="/custom/tmpl")
