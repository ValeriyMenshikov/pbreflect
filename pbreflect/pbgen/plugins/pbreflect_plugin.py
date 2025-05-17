#!/usr/bin/env python
"""Entry point for the pbreflect protoc plugin."""

import sys

from pbreflect.pbgen.plugins.pbreflect import main as pbreflect_main


def main() -> None:
    """Main entry point for the plugin."""
    # Запускаем основной код плагина
    pbreflect_main()


if __name__ == "__main__":
    main()
