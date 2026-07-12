"""Utilities for finding files in the filesystem."""

from pathlib import Path


class ProtoFileFinder:
    """Finds .proto files under a directory, excluding well-known imports."""

    def __init__(self, proto_dir: str, exclude_patterns: list[str] | None = None) -> None:
        self._proto_dir = proto_dir
        self._exclude_patterns = exclude_patterns or ["google/", "reflection.proto", "grpc/"]

    @property
    def proto_dir(self) -> str:
        return self._proto_dir

    def find_proto_files(self) -> list[str]:
        return [
            str(p)
            for p in Path(self._proto_dir).rglob("*.proto")
            if p.is_file() and not any(pat in str(p) for pat in self._exclude_patterns)
        ]
