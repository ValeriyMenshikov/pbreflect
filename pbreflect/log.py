"""Logging configuration."""

import logging
import os


def _setup() -> None:
    level_name = os.environ.get("PBREFLECT_LOG_LEVEL", "DEBUG").upper()
    level = getattr(logging, level_name, logging.DEBUG)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


_setup()


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
