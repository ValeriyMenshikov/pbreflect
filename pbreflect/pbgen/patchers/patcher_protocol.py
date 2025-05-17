"""Protocol definition for code patchers."""

from typing import Protocol


class CodePatcher(Protocol):
    """Protocol for code patchers.

    All patchers should implement this protocol by providing a patch method.
    Internal implementation details should be hidden behind private methods.
    """

    def patch(self) -> None:
        """Apply all patches.

        This is the main public method that should be called to apply patches.
        The implementation should handle all the patching logic internally.
        """
        ...
