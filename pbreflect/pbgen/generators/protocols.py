"""Protocols for generator strategies."""

from typing import Protocol, TypeVar, runtime_checkable


@runtime_checkable
class GeneratorStrategy(Protocol):
    """Protocol for generator strategies."""

    @property
    def command_template(self) -> list[str]:
        """Command template for this generator.

        Returns:
            Command template as a list of arguments
        """
        ...


# Define type for generator strategies
T_GeneratorStrategy = TypeVar("T_GeneratorStrategy", bound="GeneratorStrategy")
