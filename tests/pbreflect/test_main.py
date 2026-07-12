"""Tests for CLI commands in pbreflect.main."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from pbreflect.main import cli


class TestCliGroup:
    """Tests for the CLI group."""

    def test_help_lists_commands(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "get-protos" in result.output
        assert "generate" in result.output
        assert "reflect" in result.output


class TestGetProtos:
    """Tests for get-protos command."""

    @patch("pbreflect.main.RecoverService")
    def test_successful_recovery(self, mock_service_cls: MagicMock) -> None:
        from pathlib import Path

        mock_service = mock_service_cls.return_value.__enter__.return_value
        mock_service.recover_proto_files.return_value = [Path("a.proto"), Path("b.proto")]

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["get-protos", "-h", "localhost:50051", "-o", "protos"])

        assert result.exit_code == 0
        assert "2 proto files" in result.output

    @patch("pbreflect.main.RecoverService")
    def test_no_protos_recovered(self, mock_service_cls: MagicMock) -> None:
        mock_service = mock_service_cls.return_value.__enter__.return_value
        mock_service.recover_proto_files.return_value = []

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["get-protos", "-h", "localhost:50051"])

        assert result.exit_code == 0
        assert "No proto files" in result.output

    @patch("pbreflect.main.RecoverService")
    def test_error_during_recovery(self, mock_service_cls: MagicMock) -> None:
        mock_service = mock_service_cls.return_value.__enter__.return_value
        mock_service.recover_proto_files.side_effect = RuntimeError("fail")

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["get-protos", "-h", "localhost:50051"])

        assert result.exit_code != 0


class TestGen:
    """Tests for generate command."""

    @patch("pbreflect.main.GenerationPipeline")
    def test_generate_runs_pipeline(self, mock_pipeline_cls: MagicMock) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, [
                "generate",
                "-p", "protos",
                "-o", "output",
            ])

        assert result.exit_code == 0
        mock_pipeline_cls.return_value.run.assert_called_once()

    @patch("pbreflect.main.GenerationPipeline")
    def test_generate_with_gen_tests(self, mock_pipeline_cls: MagicMock) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, [
                "generate",
                "-p", "protos",
                "-o", "output",
                "--gen-tests",
            ])

        assert result.exit_code == 0
        mock_pipeline_cls.return_value.run.assert_called_once()


class TestReflect:
    """Tests for reflect command."""

    @patch("pbreflect.main.GenerationPipeline")
    @patch("pbreflect.main.RecoverService")
    def test_reflect_generates_from_server(self, mock_service_cls: MagicMock, mock_pipeline_cls: MagicMock) -> None:
        from pathlib import Path

        mock_service = mock_service_cls.return_value.__enter__.return_value
        mock_service.recover_proto_files.return_value = [Path("a.proto")]

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, [
                "reflect",
                "-h", "localhost:50051",
                "-o", "clients",
            ])

        assert result.exit_code == 0
        mock_pipeline_cls.return_value.run.assert_called_once()

    @patch("pbreflect.main.RecoverService")
    def test_reflect_no_protos_recovered(self, mock_service_cls: MagicMock) -> None:
        mock_service = mock_service_cls.return_value.__enter__.return_value
        mock_service.recover_proto_files.return_value = []

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, [
                "reflect",
                "-h", "localhost:50051",
            ])

        assert result.exit_code == 0
        assert "No proto files" in result.output


class TestTlsFlags:
    """Tests for _tls_flags helper."""

    def test_returns_true_when_certs_provided(self) -> None:
        from pathlib import Path

        from pbreflect.main import _tls_flags

        runner = CliRunner()
        with runner.isolated_filesystem():
            cert = Path("cert.pem")
            cert.write_text("fake")
            result = _tls_flags(False, cert, None, None)
            assert result is True

    def test_returns_use_tls_when_no_certs(self) -> None:
        from pbreflect.main import _tls_flags

        assert _tls_flags(True, None, None, None) is True
        assert _tls_flags(False, None, None, None) is False
