"""Tests for GeneratorFactory and GeneratorType."""

import pytest

from pbreflect.pbgen.generators.factory import GeneratorFactory, GeneratorType
from pbreflect.pbgen.generators.strategies.betterproto import BetterProtoGeneratorStrategy
from pbreflect.pbgen.generators.strategies.default import DefaultGeneratorStrategy
from pbreflect.pbgen.generators.strategies.mypy import MyPyGeneratorStrategy
from pbreflect.pbgen.generators.strategies.pbreflect import PbReflectGeneratorStrategy


class TestGeneratorType:
    """Tests for GeneratorType enum."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("default", GeneratorType.DEFAULT),
            ("mypy", GeneratorType.MYPY),
            ("betterproto", GeneratorType.BETTERPROTO),
            ("pbreflect", GeneratorType.PBREFLECT),
        ],
    )
    def test_from_str_valid(self, value: str, expected: GeneratorType) -> None:
        assert GeneratorType.from_str(value) == expected

    def test_from_str_invalid_raises(self) -> None:
        with pytest.raises(ValueError):
            GeneratorType.from_str("nonexistent")

    def test_values_are_unique(self) -> None:
        values = [e.value for e in GeneratorType]
        assert len(values) == len(set(values))


class TestGeneratorFactory:
    """Tests for GeneratorFactory.create_generator."""

    @pytest.mark.parametrize(
        ("gen_type", "expected_cls"),
        [
            (GeneratorType.PBREFLECT, PbReflectGeneratorStrategy),
            (GeneratorType.DEFAULT, DefaultGeneratorStrategy),
            (GeneratorType.MYPY, MyPyGeneratorStrategy),
            (GeneratorType.BETTERPROTO, BetterProtoGeneratorStrategy),
        ],
    )
    def test_creates_correct_strategy(self, gen_type: GeneratorType, expected_cls: type) -> None:
        strategy = GeneratorFactory.create_generator(gen_type)
        assert isinstance(strategy, expected_cls)

    def test_pbreflect_passes_async_mode(self) -> None:
        strategy = GeneratorFactory.create_generator(GeneratorType.PBREFLECT, async_mode=False)
        assert isinstance(strategy, PbReflectGeneratorStrategy)
        assert strategy.async_mode is False

    def test_pbreflect_passes_template_dir(self) -> None:
        strategy = GeneratorFactory.create_generator(
            GeneratorType.PBREFLECT, template_dir="/custom/templates"
        )
        assert isinstance(strategy, PbReflectGeneratorStrategy)
        assert strategy.template_dir == "/custom/templates"

    def test_all_strategies_satisfy_protocol(self) -> None:
        for gen_type in GeneratorType:
            strategy = GeneratorFactory.create_generator(gen_type)
            assert hasattr(strategy, "command_template")
            assert isinstance(strategy.command_template, list)
