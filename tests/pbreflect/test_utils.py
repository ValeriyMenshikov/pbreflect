"""Tests for pbreflect.utils string conversion functions."""

import pytest

from pbreflect.utils import name_to_snake, snake_to_camel


class TestNameToSnake:
    """Tests for name_to_snake."""

    @pytest.mark.parametrize(
        ("input_val", "expected"),
        [
            ("CamelCase", "camel_case"),
            ("PascalCase", "pascal_case"),
            ("already_snake", "already_snake"),
            ("HTTPServer", "http_server"),
            ("getHTTPResponse", "get_http_response"),
            ("simple", "simple"),
            ("With Spaces", "with_spaces"),
            ("with.dots", "with_dots"),
            ("with/slashes", "with_slashes"),
            ("with-dashes", "with_dashes"),
            ("A", "a"),
            ("", ""),
            ("ABC", "abc"),
            ("XMLParser", "xml_parser"),
            ("parseXMLString", "parse_xml_string"),
        ],
    )
    def test_conversion(self, input_val: str, expected: str) -> None:
        assert name_to_snake(input_val) == expected

    def test_special_chars_replaced(self) -> None:
        assert name_to_snake("AT&T") == "atandt"

    def test_braces_removed(self) -> None:
        assert name_to_snake("{placeholder}") == "placeholder"


class TestSnakeToCamel:
    """Tests for snake_to_camel."""

    @pytest.mark.parametrize(
        ("input_val", "expected"),
        [
            ("snake_case", "SnakeCase"),
            ("already_camel", "AlreadyCamel"),
            ("simple", "Simple"),
            ("with_numbers_123", "WithNumbers123"),
            ("", ""),
            ("a", "A"),
            ("http_server", "HttpServer"),
        ],
    )
    def test_conversion(self, input_val: str, expected: str) -> None:
        assert snake_to_camel(input_val) == expected
