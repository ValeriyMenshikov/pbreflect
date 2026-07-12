"""Tests for pbreflect_plugin entry point."""

from unittest.mock import MagicMock, patch

from pbreflect.pbgen.plugins.pbreflect_plugin import main


class TestPbReflectPluginMain:
    """Tests for pbreflect_plugin.main."""

    @patch("pbreflect.pbgen.plugins.pbreflect_plugin.pbreflect_main")
    def test_calls_pbreflect_main(self, mock_main: MagicMock) -> None:
        main()
        mock_main.assert_called_once()
