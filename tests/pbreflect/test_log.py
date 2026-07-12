"""Tests for log module."""

import importlib
import logging

import pytest

from pbreflect.log import get_logger


class TestGetLogger:
    """Tests for get_logger."""

    def test_returns_logger_with_name(self) -> None:
        logger = get_logger("test.module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"

    def test_returns_same_logger_for_same_name(self) -> None:
        logger1 = get_logger("test.same")
        logger2 = get_logger("test.same")
        assert logger1 is logger2


class TestSetup:
    """Tests for logging setup."""

    def test_log_level_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import pbreflect.log

        monkeypatch.setenv("PBREFLECT_LOG_LEVEL", "WARNING")
        importlib.reload(pbreflect.log)

        logger = pbreflect.log.get_logger("test.env")
        assert logger.getEffectiveLevel() == logging.WARNING

        monkeypatch.setenv("PBREFLECT_LOG_LEVEL", "DEBUG")
        importlib.reload(pbreflect.log)
