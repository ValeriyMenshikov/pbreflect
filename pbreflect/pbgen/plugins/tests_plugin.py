#!/usr/bin/env python
"""Entry point for the pbreflect-tests protoc plugin."""

from pbreflect.pbgen.plugins.tests import main as tests_main


def main() -> None:
    """Main entry point for the tests plugin."""
    tests_main()


if __name__ == "__main__":
    main()
