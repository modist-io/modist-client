# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains tests for the module log client."""

from unittest.mock import MagicMock, patch

import loguru
import pytest

from modist.log.client import (
    LOGGER_DEFAULT_CONFIG,
    configure_logger,
    get_logger,
    instance,
)


@patch("modist.log.client.loguru.logger.configure")
def test_configure_logger(mocked_configure: MagicMock):
    """Ensure configure_logger configures the loguru logger."""

    configure_logger()
    mocked_configure.assert_called_once_with(**LOGGER_DEFAULT_CONFIG)


def test_configure_logger_raises_ValueError_with_both_propagate_and_intercept():
    """Ensure configure_logger raises ValueError with both propagate and intercept."""

    with pytest.raises(ValueError):
        configure_logger(propagate=True, intercept=True)


@patch("modist.log.captures.python_warnings.capture")
@patch("modist.log.captures.python_warnings.release")
def test_configure_logger_captures_warnings(
    mocked_release: MagicMock, mocked_capture: MagicMock,
):
    """Ensure calling configure_logger with capture_warnings works."""

    configure_logger(capture_warnings=True)
    mocked_capture.assert_called_once_with(loguru.logger)
    mocked_release.assert_not_called()

    mocked_capture.reset_mock()
    configure_logger(capture_warnings=False)
    mocked_capture.assert_not_called()
    mocked_release.assert_called_once()


@patch("modist.log.handles.python_logging.PropagateHandler.add_handle")
@patch("modist.log.handles.python_logging.PropagateHandler.remove_handle")
def test_configure_logger_propagate(
    mocked_remove_handle: MagicMock, mocked_add_handle: MagicMock
):
    """Ensure calling configure_logger with propagate works."""

    configure_logger(propagate=True)
    mocked_add_handle.assert_called_once_with(loguru.logger)
    mocked_remove_handle.assert_not_called()

    mocked_add_handle.reset_mock()
    configure_logger(propagate=False)
    mocked_add_handle.assert_not_called()
    mocked_remove_handle.assert_called_once_with(loguru.logger)


@patch("modist.log.handles.python_logging.InterceptHandler.add_handle")
@patch("modist.log.handles.python_logging.InterceptHandler.remove_handle")
def test_configure_logger_intercept(
    mocked_remove_handle: MagicMock, mocked_add_handle: MagicMock
):
    """Ensure calling configure_logger with intercept works."""

    configure_logger(intercept=True)
    mocked_add_handle.assert_called_once_with(loguru.logger)
    mocked_remove_handle.assert_not_called()

    mocked_add_handle.reset_mock()
    configure_logger(intercept=False)
    mocked_add_handle.assert_not_called()
    mocked_remove_handle.assert_called_once_with(loguru.logger)


def test_get_logger():
    """Ensure get_logger works."""

    get_logger.cache_clear()
    assert get_logger() == loguru.logger


@patch("modist.log.client.patch_logger")
def test_get_logger_patches_logger(mocked_patch_logger: MagicMock):
    """Ensure the logger from get_logger will attempt to patch itself."""

    get_logger.cache_clear()
    get_logger()
    mocked_patch_logger.assert_called_once_with(loguru.logger)


def test_get_logger_remaps_warn_callable():
    """Ensure the logger from get_logger contains a remapped ``warn`` callable."""

    get_logger.cache_clear()
    log = get_logger()

    assert hasattr(log, "warn")
    assert log.warn == loguru.logger.warning


def test_instance():
    """Ensure the global log instance is what we expect."""

    get_logger.cache_clear()
    assert instance == loguru.logger
    assert get_logger() == instance
