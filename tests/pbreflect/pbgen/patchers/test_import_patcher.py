"""Tests for ImportPatcher."""

from pathlib import Path

from pbreflect.pbgen.patchers.import_patcher import ImportPatcher


class TestImportPatcher:
    """Tests for ImportPatcher.patch."""

    def test_patches_non_blacklisted_imports(self, tmp_path: Path) -> None:
        root = tmp_path / "project"
        code_dir = root / "clients"
        code_dir.mkdir(parents=True)
        test_file = code_dir / "service_pb2.py"
        test_file.write_text("from my_api import Service\n")

        patcher = ImportPatcher(str(code_dir), root)
        patcher.patch()

        content = test_file.read_text()
        assert "from clients.my_api import Service" in content

    def test_skips_blacklisted_imports(self, tmp_path: Path) -> None:
        root = tmp_path / "project"
        code_dir = root / "clients"
        code_dir.mkdir(parents=True)
        test_file = code_dir / "service_pb2.py"
        test_file.write_text("from google.protobuf import empty_pb2\nfrom grpc import Channel\n")

        patcher = ImportPatcher(str(code_dir), root)
        patcher.patch()

        content = test_file.read_text()
        assert "from google.protobuf import empty_pb2" in content
        assert "from grpc import Channel" in content

    def test_skips_already_prefixed_imports(self, tmp_path: Path) -> None:
        root = tmp_path / "project"
        code_dir = root / "clients"
        code_dir.mkdir(parents=True)
        test_file = code_dir / "service_pb2.py"
        test_file.write_text("from clients.my_api import Service\n")

        patcher = ImportPatcher(str(code_dir), root)
        patcher.patch()

        content = test_file.read_text()
        assert "from clients.my_api import Service" in content


class TestGetImports:
    """Tests for ImportPatcher._get_imports."""

    def test_extracts_from_imports(self, tmp_path: Path) -> None:
        f = tmp_path / "test.py"
        f.write_text("from foo.bar import Baz\nfrom google.protobuf import empty_pb2\n")
        imports = ImportPatcher._get_imports(f)
        assert "foo.bar" in imports
        assert "google.protobuf" in imports

    def test_no_imports_returns_empty(self, tmp_path: Path) -> None:
        f = tmp_path / "test.py"
        f.write_text("print('hello')\n")
        assert ImportPatcher._get_imports(f) == []


class TestReplaceImport:
    """Tests for ImportPatcher._replace_import."""

    def test_replaces_import(self, tmp_path: Path) -> None:
        f = tmp_path / "test.py"
        f.write_text("from foo import Bar\n")
        ImportPatcher._replace_import("foo", "clients.foo", f)
        assert "from clients.foo import Bar" in f.read_text()
