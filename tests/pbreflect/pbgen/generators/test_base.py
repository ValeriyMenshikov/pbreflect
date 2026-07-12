"""Tests for ClientGenerator."""

from pathlib import Path
from unittest.mock import MagicMock, create_autospec

import pytest

from pbreflect.pbgen.errors import GenerationFailedError, NoProtoFilesError
from pbreflect.pbgen.generators.base import ClientGenerator
from pbreflect.pbgen.generators.protocols import CommandExecutor, ProtoFileFinder


class TestClientGeneratorGenerate:
    """Tests for ClientGenerator.generate."""

    def test_raises_no_proto_files_when_empty(self, tmp_path: Path) -> None:
        mock_finder = create_autospec(ProtoFileFinder, instance=True)
        mock_finder.find_proto_files.return_value = []
        mock_finder.proto_dir = str(tmp_path / "protos")
        mock_executor = create_autospec(CommandExecutor, instance=True)

        generator = ClientGenerator(mock_finder, mock_executor)
        with pytest.raises(NoProtoFilesError):
            generator.generate(str(tmp_path / "output"), MagicMock(command_template=[]))

    def test_executes_command_for_each_proto(self, tmp_path: Path) -> None:
        mock_finder = create_autospec(ProtoFileFinder, instance=True)
        mock_finder.find_proto_files.return_value = ["a.proto", "b.proto"]
        mock_finder.proto_dir = str(tmp_path / "protos")
        mock_executor = create_autospec(CommandExecutor, instance=True)
        mock_executor.execute.return_value = (0, "")

        mock_strategy = MagicMock()
        mock_strategy.command_template = [
            "protoc",
            "--proto_path={include}",
            "--python_out={output}",
            "{proto}",
        ]

        generator = ClientGenerator(mock_finder, mock_executor)
        generator.generate(str(tmp_path / "output"), mock_strategy)

        assert mock_executor.execute.call_count == 2

    def test_raises_generation_failed_on_nonzero_exit(self, tmp_path: Path) -> None:
        mock_finder = create_autospec(ProtoFileFinder, instance=True)
        mock_finder.find_proto_files.return_value = ["a.proto"]
        mock_finder.proto_dir = str(tmp_path / "protos")
        mock_executor = create_autospec(CommandExecutor, instance=True)
        mock_executor.execute.return_value = (1, "compilation error")

        mock_strategy = MagicMock()
        mock_strategy.command_template = ["protoc", "{proto}"]

        generator = ClientGenerator(mock_finder, mock_executor)
        with pytest.raises(GenerationFailedError, match="compilation error"):
            generator.generate(str(tmp_path / "output"), mock_strategy)

    def test_command_args_formatted_correctly(self, tmp_path: Path) -> None:
        proto_dir = str(tmp_path / "protos")
        output_dir = str(tmp_path / "output")
        mock_finder = create_autospec(ProtoFileFinder, instance=True)
        mock_finder.find_proto_files.return_value = [f"{proto_dir}/a.proto"]
        mock_finder.proto_dir = proto_dir
        mock_executor = create_autospec(CommandExecutor, instance=True)
        mock_executor.execute.return_value = (0, "")

        mock_strategy = MagicMock()
        mock_strategy.command_template = [
            "protoc",
            "--proto_path={include}",
            "--python_out={output}",
            "{proto}",
        ]

        generator = ClientGenerator(mock_finder, mock_executor)
        generator.generate(output_dir, mock_strategy)

        expected_args = ["protoc", f"--proto_path={proto_dir}", f"--python_out={output_dir}", f"{proto_dir}/a.proto"]
        mock_executor.execute.assert_called_once_with(expected_args)
