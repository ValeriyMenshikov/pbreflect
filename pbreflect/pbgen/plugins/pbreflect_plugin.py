#!/usr/bin/env python
"""Entry point for the pbreflect protoc plugin."""

from pbreflect.pbgen.plugins.pbreflect import main as pbreflect_main


def main() -> None:
    """Main entry point for the plugin."""
    # Run the main plugin code
    pbreflect_main()


if __name__ == "__main__":
    main()
