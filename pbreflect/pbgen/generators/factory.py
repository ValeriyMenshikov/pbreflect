"""Factory for creating generator strategies."""

from pathlib import Path
from typing import Type

from pbreflect.pbgen.generators.strategies.betterproto import BetterProtoGeneratorStrategy
from pbreflect.pbgen.generators.strategies.default import DefaultGeneratorStrategy
from pbreflect.pbgen.generators.strategies.dynamic import DynamicGeneratorStrategy
from pbreflect.pbgen.generators.strategies.mypy import MyPyGeneratorStrategy


class GeneratorFactoryImpl:
    """Implementation of generator factory."""

    def __init__(self) -> None:
        """Initialize the generator factory."""
        self.strategies = {
            "default": DefaultGeneratorStrategy,
            "mypy": MyPyGeneratorStrategy,
            "betterproto": BetterProtoGeneratorStrategy,
        }

    def create_generator(self, gen_type: str, root_path: Path):
        """Create a generator strategy based on the specified type.

        Args:
            gen_type: Type of generator to create
            root_path: Root project directory (kept for compatibility)

        Returns:
            Generator strategy

        Raises:
            ValueError: If the generator type is not supported
        """
        if gen_type in self.strategies:
            return self.strategies[gen_type]()
        
        # For custom generators, use dynamic strategy
        return DynamicGeneratorStrategy(gen_type)
