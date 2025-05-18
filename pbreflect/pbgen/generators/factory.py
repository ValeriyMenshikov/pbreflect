"""Factory for creating generator strategies."""

from typing import Any

from pbreflect.pbgen.generators.protocols import GeneratorStrategy
from pbreflect.pbgen.generators.strategies.betterproto import BetterProtoGeneratorStrategy
from pbreflect.pbgen.generators.strategies.default import DefaultGeneratorStrategy
from pbreflect.pbgen.generators.strategies.dynamic import DynamicGeneratorStrategy
from pbreflect.pbgen.generators.strategies.mypy import MyPyGeneratorStrategy
from pbreflect.pbgen.generators.strategies.pbreflect import PbReflectGeneratorStrategy


class GeneratorFactoryImpl:
    """Implementation of generator factory."""

    def __init__(self) -> None:
        self.strategies: dict[str, type[GeneratorStrategy]] = {
            "default": DefaultGeneratorStrategy,
            "mypy": MyPyGeneratorStrategy,
            "betterproto": BetterProtoGeneratorStrategy,
            "pbreflect": PbReflectGeneratorStrategy,
        }

    def create_generator(self, gen_type: str, **kwargs: Any) -> GeneratorStrategy:
        """Create a generator strategy based on the specified type.

        Args:
            gen_type: Type of generator to create
            **kwargs: Additional parameters to pass to the generator strategy

        Returns:
            Generator strategy

        Raises:
            ValueError: If the generator type is not supported
        """
        if gen_type in self.strategies:
            strategy_class = self.strategies[gen_type]

            # Handle special case for PbReflectGeneratorStrategy
            if gen_type == "pbreflect":
                async_mode = kwargs.get("async_mode", True)
                return PbReflectGeneratorStrategy(async_mode=async_mode)

            return strategy_class()

        dynamic_strategy = DynamicGeneratorStrategy(gen_type)
        assert isinstance(dynamic_strategy, GeneratorStrategy)
        return dynamic_strategy
