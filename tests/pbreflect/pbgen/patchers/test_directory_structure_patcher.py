"""Tests for DirectoryStructurePatcher."""

from pathlib import Path

from pbreflect.pbgen.patchers.directory_structure_patcher import DirectoryStructurePatcher


class TestDirectoryStructurePatcher:
    """Tests for DirectoryStructurePatcher.patch."""

    def test_moves_files_from_dotted_dirs(self, tmp_path: Path) -> None:
        dotted_dir = tmp_path / "com" / "example.api"
        dotted_dir.mkdir(parents=True)
        (dotted_dir / "service_pb2_pbreflect.py").write_text("# test")

        patcher = DirectoryStructurePatcher(str(tmp_path))
        patcher.patch()

        expected = tmp_path / "com" / "example" / "api" / "service_pb2_pbreflect.py"
        assert expected.exists()
        assert not dotted_dir.exists()

    def test_no_dotted_dirs_no_changes(self, tmp_path: Path) -> None:
        normal_dir = tmp_path / "normal"
        normal_dir.mkdir()
        (normal_dir / "file.py").write_text("# test")

        patcher = DirectoryStructurePatcher(str(tmp_path))
        patcher.patch()

        assert (normal_dir / "file.py").exists()

    def test_empty_dir_no_changes(self, tmp_path: Path) -> None:
        patcher = DirectoryStructurePatcher(str(tmp_path))
        patcher.patch()
        assert tmp_path.exists()
