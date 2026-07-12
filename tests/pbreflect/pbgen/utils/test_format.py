"""Tests for format_file."""

from unittest.mock import MagicMock, patch

from pbreflect.pbgen.utils.format import format_file


class TestFormatFile:
    """Tests for format_file."""

    @patch("pbreflect.pbgen.utils.format.CommandExecutor")
    def test_format_without_suffix(self, mock_executor_cls: MagicMock) -> None:
        mock_executor = mock_executor_cls.return_value
        format_file("/output")
        mock_executor.execute.assert_any_call(["ruff", "format", "/output"])
        mock_executor.execute.assert_any_call(["ruff", "check", "/output", "--fix"])

    @patch("pbreflect.pbgen.utils.format.CommandExecutor")
    @patch("pbreflect.pbgen.utils.format.os.walk")
    def test_format_with_suffix(self, mock_walk: MagicMock, mock_executor_cls: MagicMock) -> None:
        mock_walk.return_value = [("/output", [], ["a_pbreflect.py", "b_pbreflect.py"])]
        mock_executor = mock_executor_cls.return_value
        format_file("/output", "_pbreflect.py")

        mock_executor.execute.assert_any_call(
            ["ruff", "format", "/output/a_pbreflect.py", "/output/b_pbreflect.py"]
        )

    @patch("pbreflect.pbgen.utils.format.CommandExecutor")
    @patch("pbreflect.pbgen.utils.format.os.walk")
    def test_format_with_suffix_no_matching_files(self, mock_walk: MagicMock, mock_executor_cls: MagicMock) -> None:
        mock_walk.return_value = [("/output", [], ["other.txt"])]
        mock_executor = mock_executor_cls.return_value
        format_file("/output", "_pbreflect.py")

        mock_executor.execute.assert_not_called()
