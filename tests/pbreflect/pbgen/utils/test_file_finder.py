"""Tests for ProtoFileFinder."""

from pathlib import Path

from pbreflect.pbgen.utils.file_finder import ProtoFileFinder


class TestProtoFileFinder:
    """Tests for ProtoFileFinder."""

    def test_finds_proto_files(self, tmp_path: Path) -> None:
        (tmp_path / "a.proto").write_text('syntax = "proto3";')
        (tmp_path / "b.proto").write_text('syntax = "proto3";')
        (tmp_path / "not_proto.txt").write_text("ignore me")

        finder = ProtoFileFinder(str(tmp_path))
        result = finder.find_proto_files()
        assert len(result) == 2
        assert all(p.endswith(".proto") for p in result)

    def test_excludes_google_protos(self, tmp_path: Path) -> None:
        google_dir = tmp_path / "google"
        google_dir.mkdir()
        (google_dir / "empty.proto").write_text('syntax = "proto3";')
        (tmp_path / "my.proto").write_text('syntax = "proto3";')

        finder = ProtoFileFinder(str(tmp_path))
        result = finder.find_proto_files()
        assert len(result) == 1
        assert "my.proto" in result[0]

    def test_excludes_reflection_proto(self, tmp_path: Path) -> None:
        (tmp_path / "reflection.proto").write_text('syntax = "proto3";')
        (tmp_path / "my.proto").write_text('syntax = "proto3";')

        finder = ProtoFileFinder(str(tmp_path))
        result = finder.find_proto_files()
        assert len(result) == 1
        assert "my.proto" in result[0]

    def test_excludes_grpc_protos(self, tmp_path: Path) -> None:
        grpc_dir = tmp_path / "grpc"
        grpc_dir.mkdir()
        (grpc_dir / "service.proto").write_text('syntax = "proto3";')
        (tmp_path / "my.proto").write_text('syntax = "proto3";')

        finder = ProtoFileFinder(str(tmp_path))
        result = finder.find_proto_files()
        assert len(result) == 1
        assert "my.proto" in result[0]

    def test_finds_nested_protos(self, tmp_path: Path) -> None:
        nested = tmp_path / "sub" / "dir"
        nested.mkdir(parents=True)
        (nested / "deep.proto").write_text('syntax = "proto3";')

        finder = ProtoFileFinder(str(tmp_path))
        result = finder.find_proto_files()
        assert len(result) == 1
        assert "deep.proto" in result[0]

    def test_empty_dir_returns_empty_list(self, tmp_path: Path) -> None:
        finder = ProtoFileFinder(str(tmp_path))
        assert finder.find_proto_files() == []

    def test_proto_dir_property(self, tmp_path: Path) -> None:
        finder = ProtoFileFinder(str(tmp_path))
        assert finder.proto_dir == str(tmp_path)

    def test_custom_exclude_patterns(self, tmp_path: Path) -> None:
        (tmp_path / "skip_me.proto").write_text('syntax = "proto3";')
        (tmp_path / "keep.proto").write_text('syntax = "proto3";')

        finder = ProtoFileFinder(str(tmp_path), exclude_patterns=["skip_me"])
        result = finder.find_proto_files()
        assert len(result) == 1
        assert "keep.proto" in result[0]
