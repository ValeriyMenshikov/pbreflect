"""Utilities for finding files in the filesystem."""

from pathlib import Path


class ProtoFileFinderImpl:
    """Implementation of proto file finder."""

    def __init__(self, proto_dir: str, exclude_patterns: list[str] | None = None) -> None:
        """Initialize the proto file finder.

        Args:
            proto_dir: Directory to search for proto files
            exclude_patterns: List of patterns to exclude from search results
        """
        self.proto_dir = proto_dir
        self.exclude_patterns = exclude_patterns or ["google/", "reflection.proto", "grpc/"]

    def find_proto_files(self) -> list[str]:
        """Find all proto files in the proto directory.

        Returns:
            List of paths to proto files
        """
        proto_files = []
        for proto_path in Path(self.proto_dir).rglob("*.proto"):
            if not proto_path.is_file():
                continue

            # Skip excluded patterns
            if any(pattern in str(proto_path) for pattern in self.exclude_patterns):
                continue

            proto_files.append(str(proto_path))

        return proto_files
