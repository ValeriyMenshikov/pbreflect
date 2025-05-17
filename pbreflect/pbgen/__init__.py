"""Protocol Buffer Code Generation Module.

This module provides tools for generating client code from Protocol Buffer definitions.
It includes generators, plugins, and utilities for creating Python client libraries.
"""

from pbreflect.pbgen.errors import GenerationFailedError, NoProtoFilesError

__all__ = ["GenerationFailedError", "NoProtoFilesError"]
