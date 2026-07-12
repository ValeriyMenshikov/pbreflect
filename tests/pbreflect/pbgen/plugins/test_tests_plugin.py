"""Tests for tests_plugin entry point."""

from unittest.mock import MagicMock, patch

from pbreflect.pbgen.plugins.tests_plugin import main


class TestTestsPluginMain:
    """Tests for tests_plugin.main."""

    @patch("pbreflect.pbgen.plugins.tests_plugin.tests_main")
    def test_calls_tests_main(self, mock_main: MagicMock) -> None:
        main()
        mock_main.assert_called_once()
