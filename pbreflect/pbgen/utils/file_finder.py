"""Utilities for finding files in the filesystem."""

from pathlib import Path


class ProtoFileFinderImpl:
    """Implementation of proto file finder."""

    def __init__(self, exclude_patterns: list[str] | None = None) -> None:
        """Initialize the proto file finder.

        Args:
            exclude_patterns: List of patterns to exclude from search results
        """
        self.exclude_patterns = exclude_patterns or ["google/protobuf/descriptor.proto"]

    def find_proto_files(self, include_dir: str) -> list[Path]:
        """Find all proto files in the specified directory.

        Args:
            include_dir: Directory to search for proto files

        Returns:
            List of paths to proto files
        """
        proto_files = []
        for proto_path in Path(include_dir).rglob("*.proto"):
            if not proto_path.is_file():
                continue

            # Skip excluded patterns
            if any(pattern in str(proto_path) for pattern in self.exclude_patterns):
                continue

            proto_files.append(proto_path)

        return proto_files
