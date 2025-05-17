"""Factory for creating generator strategies."""


from pbreflect.pbgen.generators.protocols import GeneratorStrategy
from pbreflect.pbgen.generators.strategies.betterproto import BetterProtoGeneratorStrategy
from pbreflect.pbgen.generators.strategies.default import DefaultGeneratorStrategy
from pbreflect.pbgen.generators.strategies.dynamic import DynamicGeneratorStrategy
from pbreflect.pbgen.generators.strategies.mypy import MyPyGeneratorStrategy


class GeneratorFactoryImpl:
    """Implementation of generator factory."""

    def __init__(self) -> None:
        """Initialize the generator factory."""
        self.strategies: dict[str, type[GeneratorStrategy]] = {
            "default": DefaultGeneratorStrategy,
            "mypy": MyPyGeneratorStrategy,
            "betterproto": BetterProtoGeneratorStrategy,
        }

    def create_generator(self, gen_type: str) -> GeneratorStrategy:
        """Create a generator strategy based on the specified type.

        Args:
            gen_type: Type of generator to create

        Returns:
            Generator strategy

        Raises:
            ValueError: If the generator type is not supported
        """
        if gen_type in self.strategies:
            return self.strategies[gen_type]()

        # For custom generators, use dynamic strategy
        # Явно указываем тип для mypy
        dynamic_strategy = DynamicGeneratorStrategy(gen_type)
        # Используем assert для проверки типа во время выполнения
        assert isinstance(dynamic_strategy, GeneratorStrategy)
        return dynamic_strategy
