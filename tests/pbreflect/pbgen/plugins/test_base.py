"""Tests for TemplateRenderer and parse_plugin_parameters."""

from pathlib import Path

from pbreflect.pbgen.plugins.base import TemplateRenderer, parse_plugin_parameters


class TestParsePluginParameters:
    """Tests for parse_plugin_parameters."""

    def test_empty_string_returns_empty_dict(self) -> None:
        assert parse_plugin_parameters("") == {}

    def test_single_key_value(self) -> None:
        result = parse_plugin_parameters("async=true")
        assert result == {"async": "true"}

    def test_multiple_key_values(self) -> None:
        result = parse_plugin_parameters("async=false,t=/custom/dir")
        assert result == {"async": "false", "t": "/custom/dir"}

    def test_flag_without_value(self) -> None:
        result = parse_plugin_parameters("verbose")
        assert result == {"verbose": True}

    def test_mixed_flags_and_values(self) -> None:
        result = parse_plugin_parameters("verbose,async=true,t=/custom/tmpl")
        assert result == {"verbose": True, "async": "true", "t": "/custom/tmpl"}

    def test_strips_whitespace(self) -> None:
        result = parse_plugin_parameters(" async = true , t = /custom/tmpl ")
        assert result == {"async": "true", "t": "/custom/tmpl"}


class TestTemplateRenderer:
    """Tests for TemplateRenderer."""

    def test_renders_template_from_default_dir(self, tmp_path: Path) -> None:
        template_file = tmp_path / "test.j2"
        template_file.write_text("Hello, {{ name }}!")
        renderer = TemplateRenderer(default_dir=tmp_path)
        assert renderer.render("test.j2", name="World") == "Hello, World!"

    def test_uses_custom_dir_when_provided(self, tmp_path: Path) -> None:
        default_dir = tmp_path / "default"
        custom_dir = tmp_path / "custom"
        default_dir.mkdir()
        custom_dir.mkdir()
        (default_dir / "test.j2").write_text("default")
        (custom_dir / "test.j2").write_text("custom {{ name }}")

        renderer = TemplateRenderer(default_dir=default_dir, custom_dir=str(custom_dir))
        assert renderer.render("test.j2", name="tmpl") == "custom tmpl"

    def test_extra_filters_registered(self, tmp_path: Path) -> None:
        (tmp_path / "test.j2").write_text("{{ value | upper }}")
        renderer = TemplateRenderer(
            default_dir=tmp_path,
            extra_filters={"upper": str.upper},
        )
        assert renderer.render("test.j2", value="hello") == "HELLO"
