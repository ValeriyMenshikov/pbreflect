"""Tests for generator strategies command_template."""

import pytest

from pbreflect.pbgen.generators.strategies.betterproto import BetterProtoGeneratorStrategy
from pbreflect.pbgen.generators.strategies.default import DefaultGeneratorStrategy
from pbreflect.pbgen.generators.strategies.dynamic import DynamicGeneratorStrategy
from pbreflect.pbgen.generators.strategies.mypy import MyPyGeneratorStrategy
from pbreflect.pbgen.generators.strategies.pbreflect import PbReflectGeneratorStrategy
from pbreflect.pbgen.generators.strategies.pbreflect_tests import PbReflectTestsGeneratorStrategy


class TestPbReflectGeneratorStrategy:
    """Tests for PbReflectGeneratorStrategy."""

    def test_default_command_template(self) -> None:
        strategy = PbReflectGeneratorStrategy()
        template = strategy.command_template
        assert "--pbreflect_out={output}" in template
        assert "--python_out={output}" in template
        assert "--mypy_out=readable_stubs,quiet:{output}" in template
        assert "{proto}" in template

    def test_async_false_adds_option(self) -> None:
        strategy = PbReflectGeneratorStrategy(async_mode=False)
        joined = " ".join(strategy.command_template)
        assert "async=false" in joined

    def test_template_dir_adds_option(self) -> None:
        strategy = PbReflectGeneratorStrategy(template_dir="/custom/tmpl")
        joined = " ".join(strategy.command_template)
        assert "t=/custom/tmpl" in joined

    def test_both_options_combined(self) -> None:
        strategy = PbReflectGeneratorStrategy(async_mode=False, template_dir="/custom/tmpl")
        joined = " ".join(strategy.command_template)
        assert "async=false" in joined
        assert "t=/custom/tmpl" in joined


class TestDefaultGeneratorStrategy:
    """Tests for DefaultGeneratorStrategy."""

    def test_command_template(self) -> None:
        strategy = DefaultGeneratorStrategy()
        template = strategy.command_template
        assert "--python_out={output}" in template
        assert "--grpc_python_out={output}" in template
        assert "{include}" in template
        assert "{proto}" in template


class TestMyPyGeneratorStrategy:
    """Tests for MyPyGeneratorStrategy."""

    def test_command_template(self) -> None:
        strategy = MyPyGeneratorStrategy()
        template = strategy.command_template
        assert "--mypy_out=readable_stubs,quiet:{output}" in template
        assert "--mypy_grpc_out=readable_stubs,quiet:{output}" in template
        assert "--python_out={output}" in template
        assert "--grpc_python_out={output}" in template


class TestBetterProtoGeneratorStrategy:
    """Tests for BetterProtoGeneratorStrategy."""

    def test_command_template(self) -> None:
        strategy = BetterProtoGeneratorStrategy()
        template = strategy.command_template
        assert "--python_betterproto_out={output}" in template
        assert "{include}" in template
        assert "{proto}" in template


class TestDynamicGeneratorStrategy:
    """Tests for DynamicGeneratorStrategy."""

    def test_command_template_uses_compiler_name(self) -> None:
        strategy = DynamicGeneratorStrategy(compiler="my_plugin")
        template = strategy.command_template
        joined = " ".join(template)
        assert "--my_plugin_out={output}" in joined
        assert "{include}" in joined
        assert "{proto}" in joined

    def test_different_compiler_produces_different_output(self) -> None:
        strategy = DynamicGeneratorStrategy(compiler="other")
        joined = " ".join(strategy.command_template)
        assert "--other_out={output}" in joined


class TestPbReflectTestsGeneratorStrategy:
    """Tests for PbReflectTestsGeneratorStrategy."""

    def test_command_template_contains_plugin(self) -> None:
        strategy = PbReflectTestsGeneratorStrategy()
        template = strategy.command_template
        joined = " ".join(template)
        assert "--pbreflect_tests_out=" in joined
        assert "{include}" in joined
        assert "{proto}" in joined

    def test_async_mode_adds_option(self) -> None:
        strategy = PbReflectTestsGeneratorStrategy(async_mode=True)
        joined = " ".join(strategy.command_template)
        assert "async=true" in joined

    def test_client_module_added(self) -> None:
        strategy = PbReflectTestsGeneratorStrategy(client_module="my_clients")
        joined = " ".join(strategy.command_template)
        assert "client_module=my_clients" in joined

    def test_template_dir_added(self) -> None:
        strategy = PbReflectTestsGeneratorStrategy(template_dir="/custom/tmpl")
        joined = " ".join(strategy.command_template)
        assert "t=/custom/tmpl" in joined


@pytest.mark.parametrize(
    "strategy_cls",
    [
        PbReflectGeneratorStrategy,
        DefaultGeneratorStrategy,
        MyPyGeneratorStrategy,
        BetterProtoGeneratorStrategy,
        DynamicGeneratorStrategy,
        PbReflectTestsGeneratorStrategy,
    ],
)
def test_all_strategies_have_placeholders(strategy_cls: type) -> None:
    """All strategies must include {output} and {proto} placeholders."""
    strategy = strategy_cls() if strategy_cls != DynamicGeneratorStrategy else strategy_cls(compiler="test")
    joined = " ".join(strategy.command_template)
    assert "{output}" in joined
    assert "{proto}" in joined
