"""Protocols for generator strategies."""

from typing import Protocol, runtime_checkable


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
