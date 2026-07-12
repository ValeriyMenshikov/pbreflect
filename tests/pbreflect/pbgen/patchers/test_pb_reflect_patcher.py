"""Tests for PbReflectPatcher."""

from unittest.mock import MagicMock, patch

from pbreflect.pbgen.patchers.pb_reflect_patcher import PbReflectPatcher


class TestPbReflectPatcher:
    """Tests for PbReflectPatcher.patch."""

    @patch("pbreflect.pbgen.patchers.pb_reflect_patcher.format_file")
    def test_patch_calls_format_file_with_suffix(self, mock_format: MagicMock) -> None:
        patcher = PbReflectPatcher("/output")
        patcher.patch()

        mock_format.assert_called_once_with("/output", "_pbreflect.py")

    @patch("pbreflect.pbgen.patchers.pb_reflect_patcher.format_file")
    def test_patch_preserves_output_dir(self, mock_format: MagicMock) -> None:
        patcher = PbReflectPatcher("/custom/output")
        patcher.patch()

        mock_format.assert_called_once_with("/custom/output", "_pbreflect.py")
