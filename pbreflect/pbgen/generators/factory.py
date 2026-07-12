"""Factory for creating generator strategies."""

from enum import Enum

from pbreflect.pbgen.generators.protocols import GeneratorStrategy
from pbreflect.pbgen.generators.strategies.betterproto import BetterProtoGeneratorStrategy
from pbreflect.pbgen.generators.strategies.default import DefaultGeneratorStrategy
from pbreflect.pbgen.generators.strategies.mypy import MyPyGeneratorStrategy
from pbreflect.pbgen.generators.strategies.pbreflect import PbReflectGeneratorStrategy


class GeneratorType(Enum):
    """Supported generator types."""

    DEFAULT = "default"
    MYPY = "mypy"
    BETTERPROTO = "betterproto"
    PBREFLECT = "pbreflect"

    @classmethod
    def from_str(cls, value: str) -> "GeneratorType":
        """Create a GeneratorType from a string value."""
        return cls(value)


class GeneratorFactory:
    """Creates the appropriate GeneratorStrategy for a given gen_type."""

    @staticmethod
    def create_generator(
        gen_type: GeneratorType,
        *,
        async_mode: bool = True,
        template_dir: str | None = None,
    ) -> GeneratorStrategy:
        match gen_type:
            case GeneratorType.PBREFLECT:
                return PbReflectGeneratorStrategy(async_mode=async_mode, template_dir=template_dir)
            case GeneratorType.DEFAULT:
                return DefaultGeneratorStrategy()
            case GeneratorType.MYPY:
                return MyPyGeneratorStrategy()
            case GeneratorType.BETTERPROTO:
                return BetterProtoGeneratorStrategy()
