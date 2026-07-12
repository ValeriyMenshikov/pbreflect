"""Tests for MypyPatcher."""

from pathlib import Path

from pbreflect.pbgen.patchers.mypy_patcher import MypyPatcher


class TestMypyPatcher:
    """Tests for MypyPatcher.patch."""

    def test_removes_final_decorators(self, tmp_path: Path) -> None:
        stub = tmp_path / "service_pb2.pyi"
        stub.write_text("@final\nclass Foo:\n    pass\n")

        MypyPatcher(str(tmp_path)).patch()

        content = stub.read_text()
        assert "@final" not in content
        assert "class Foo:" in content

    def test_fixes_class_names(self, tmp_path: Path) -> None:
        stub = tmp_path / "service_pb2.pyi"
        stub.write_text("class _EnumTypeWrapper:\n    pass\n")

        MypyPatcher(str(tmp_path)).patch()

        content = stub.read_text()
        assert "EnumTypeWrapper" in content
        assert "_EnumTypeWrapper" not in content

    def test_adds_class_annotations_to_pb2_stubs(self, tmp_path: Path) -> None:
        stub = tmp_path / "service_pb2.pyi"
        stub.write_text("class Foo:\n    pass\n")

        MypyPatcher(str(tmp_path)).patch()

        content = stub.read_text()
        assert "Foo: Foo" in content

    def test_no_changes_to_non_pyi_files(self, tmp_path: Path) -> None:
        py_file = tmp_path / "service.py"
        py_file.write_text("@final\nclass Foo:\n    pass\n")

        MypyPatcher(str(tmp_path)).patch()

        content = py_file.read_text()
        assert "@final" in content


class TestRemoveFinalDecorators:
    """Tests for _remove_final_decorators."""

    def test_removes_lines_with_final(self) -> None:
        content = "@final\nclass Foo:\n    pass\n"
        result = MypyPatcher._remove_final_decorators(content)
        assert "@final" not in result
        assert "class Foo:" in result

    def test_keeps_non_final_decorators(self) -> None:
        content = "@dataclass\nclass Foo:\n    pass\n"
        result = MypyPatcher._remove_final_decorators(content)
        assert "@dataclass" in result


class TestFixClassNames:
    """Tests for _fix_class_names."""

    def test_replaces_enum_type_wrapper(self) -> None:
        content = "class _EnumTypeWrapper:\n    pass\n"
        result = MypyPatcher._fix_class_names(content)
        assert "EnumTypeWrapper" in result

    def test_replaces_extension_field_descriptor(self) -> None:
        content = "class _ExtensionFieldDescriptor:\n    pass\n"
        result = MypyPatcher._fix_class_names(content)
        assert "ExtensionFieldDescriptor" in result
