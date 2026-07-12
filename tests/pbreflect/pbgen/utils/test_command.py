"""Tests for CommandExecutor."""

from unittest.mock import MagicMock, patch

from pbreflect.pbgen.utils.command import CommandExecutor


class TestCommandExecutor:
    """Tests for CommandExecutor.execute."""

    @patch("pbreflect.pbgen.utils.command.run")
    def test_returns_exit_code_and_stderr(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stderr=b"some error")
        exit_code, stderr = CommandExecutor.execute(["protoc", "--version"])
        assert exit_code == 0
        assert stderr == "some error"

    @patch("pbreflect.pbgen.utils.command.run")
    def test_empty_stderr_returns_empty_string(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stderr=b"")
        exit_code, stderr = CommandExecutor.execute(["protoc"])
        assert exit_code == 0
        assert stderr == ""

    @patch("pbreflect.pbgen.utils.command.run")
    def test_none_stderr_returns_empty_string(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stderr=None)
        exit_code, stderr = CommandExecutor.execute(["protoc"])
        assert exit_code == 0
        assert stderr == ""

    @patch("pbreflect.pbgen.utils.command.run")
    def test_nonzero_exit_code(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=1, stderr=b"failed")
        exit_code, stderr = CommandExecutor.execute(["protoc", "bad"])
        assert exit_code == 1
        assert stderr == "failed"

    @patch("pbreflect.pbgen.utils.command.run")
    def test_unicode_decode_fallback(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=1, stderr=b"\xff\xfe")
        exit_code, stderr = CommandExecutor.execute(["protoc"])
        assert exit_code == 1
        assert isinstance(stderr, str)
