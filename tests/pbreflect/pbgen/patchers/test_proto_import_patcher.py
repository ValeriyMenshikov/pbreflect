"""Tests for ProtoImportPatcher."""

from pathlib import Path

from pbreflect.pbgen.patchers.proto_import_patcher import ProtoImportPatcher


class TestProtoImportPatcher:
    """Tests for ProtoImportPatcher.patch."""

    def test_patches_incorrect_local_imports(self, tmp_path: Path) -> None:
        sub = tmp_path / "api"
        sub.mkdir()
        proto_file = sub / "service.proto"
        proto_file.write_text('import "types.proto";\n')
        (tmp_path / "types.proto").write_text('syntax = "proto3";\n')

        patcher = ProtoImportPatcher(str(tmp_path))
        patcher.patch()

        content = proto_file.read_text()
        assert 'import "types.proto"' in content

    def test_ensures_openapiv2_compat_paths(self, tmp_path: Path) -> None:
        src_dir = tmp_path / "protoc_gen_openapiv2" / "options"
        src_dir.mkdir(parents=True)
        (src_dir / "annotations.proto").write_text('syntax = "proto3";\n')

        patcher = ProtoImportPatcher(str(tmp_path))
        patcher.patch()

        dst = tmp_path / "protoc-gen-openapiv2" / "options" / "annotations.proto"
        assert dst.exists()

    def test_no_openapiv2_dir_no_changes(self, tmp_path: Path) -> None:
        patcher = ProtoImportPatcher(str(tmp_path))
        patcher.patch()
        assert not (tmp_path / "protoc-gen-openapiv2").exists()

    def test_patches_keyword_file_names(self, tmp_path: Path) -> None:
        (tmp_path / "class.proto").write_text('syntax = "proto3";\n')

        patcher = ProtoImportPatcher(str(tmp_path))
        patcher.patch()

        assert (tmp_path / "class_pb.proto").exists()

    def test_non_keyword_file_names_not_copied(self, tmp_path: Path) -> None:
        (tmp_path / "service.proto").write_text('syntax = "proto3";\n')

        patcher = ProtoImportPatcher(str(tmp_path))
        patcher.patch()

        assert not (tmp_path / "service_pb.proto").exists()


class TestGetImports:
    """Tests for _get_imports."""

    def test_extracts_imports(self, tmp_path: Path) -> None:
        f = tmp_path / "test.proto"
        f.write_text('import "google/protobuf/empty.proto";\nimport "types.proto";\n')
        imports = ProtoImportPatcher._get_imports(f)
        assert "google/protobuf/empty.proto" in imports
        assert "types.proto" in imports

    def test_no_imports_returns_empty(self, tmp_path: Path) -> None:
        f = tmp_path / "test.proto"
        f.write_text('syntax = "proto3";\n')
        assert ProtoImportPatcher._get_imports(f) == []


class TestReplaceImport:
    """Tests for _replace_import."""

    def test_replaces_import(self, tmp_path: Path) -> None:
        f = tmp_path / "test.proto"
        f.write_text('import "old/path.proto";\n')
        ProtoImportPatcher._replace_import("old/path.proto", "new/path.proto", f)
        assert 'import "new/path.proto"' in f.read_text()
