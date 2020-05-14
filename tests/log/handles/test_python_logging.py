# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains unit-tests for the module custom python logging handlers."""

import logging
from unittest.mock import MagicMock, patch

import loguru
from hypothesis import given
from hypothesis.strategies import sampled_from
from loguru._logger import Logger

from modist.log.handles.python_logging import InterceptHandler, PropagateHandler

from ..strategies import log_record


def test_PropagateHandler_propagates_log_records_from_loguru_to_python_logging(
    loguru_logger: Logger, caplog
):
    """Ensure PropgateHandler can propgate messages from loguru to Python's logging."""

    assert PropagateHandler.add_handle(loguru_logger)
    try:
        loguru_logger.info("test")

        assert len(caplog.record_tuples) == 1
        _, levelno, message = caplog.record_tuples[0]
        assert levelno == logging.INFO
        assert message == "test"
    finally:
        assert PropagateHandler.remove_handle(loguru_logger)


def test_PropagateHandler_add_handle(loguru_logger: Logger):
    """Ensure PropgateHandler add_handle works."""

    assert len(PropagateHandler._handler_reference.values()) <= 0
    assert PropagateHandler.add_handle(loguru_logger)

    try:
        assert len(PropagateHandler._handler_reference.values()) == 1
    finally:
        assert PropagateHandler.remove_handle(loguru_logger)


def test_Propagatehandler_get_config():
    """Ensure PropgateHandler default config doesn't change without tests knowing."""

    config = PropagateHandler._get_config()
    assert isinstance(config["sink"], PropagateHandler.LoggingHandler)
    assert config["sink"].level == logging.DEBUG
    assert config["format"] == "{message}"


def test_PropagateHandler_get_handler_id(loguru_logger: Logger):
    """Ensure PropagateHandler can get handled logger instance's id."""

    assert PropagateHandler._get_handler_id(loguru_logger) is None
    assert PropagateHandler.add_handle(loguru_logger)

    try:
        assert isinstance(PropagateHandler._get_handler_id(loguru_logger), int)
    finally:
        assert PropagateHandler.remove_handle(loguru_logger)


def test_PropagateHandler_is_handled(loguru_logger: Logger):
    """Ensure PropagateHandler is_handled can tell when we are handling a logger."""

    assert not PropagateHandler.is_handled(loguru_logger)
    assert PropagateHandler.add_handle(loguru_logger)

    try:
        assert PropagateHandler.is_handled(loguru_logger)
    finally:
        assert PropagateHandler.remove_handle(loguru_logger)


def test_PropagateHandler_add_handle_doesnt_add_already_handled_logger(
    loguru_logger: Logger,
):
    """Ensure PropagateHandler add_handle doesn't readd handled loggers."""

    assert PropagateHandler.add_handle(loguru_logger)

    try:
        assert not PropagateHandler.add_handle(loguru_logger)
    finally:
        assert PropagateHandler.remove_handle(loguru_logger)


def test_PropagateHandler_remove_handle(loguru_logger: Logger):
    """Ensure PropagateHandler remove_handle works."""

    assert not PropagateHandler.remove_handle(loguru_logger)
    assert PropagateHandler.add_handle(loguru_logger)
    assert PropagateHandler.remove_handle(loguru_logger)


def test_PropagateHandler_remove_handle_doesnt_remove_unhandled_logger(
    loguru_logger: Logger,
):
    """Ensure PropagateHandler remove_handle does remove unhandled loggers."""

    PropagateHandler.remove_handle(loguru_logger)
    assert not PropagateHandler.remove_handle(loguru_logger)


@patch.object(PropagateHandler, "_get_handler_id")
@patch.object(PropagateHandler, "is_handled")
def test_PropagateHandler_remove_handle_doesnt_remove_logger_with_missing_handler_id(
    mocked_is_handled, mocked_get_handler_id, loguru_logger: Logger,
):
    """Ensure PropagateHandler remove_handle doesnt remove handler with no stored id."""

    mocked_is_handled.return_value = True
    mocked_get_handler_id.return_value = None

    assert not PropagateHandler.remove_handle(loguru_logger)


def test_PropagateHandler_remove_handle_passes_on_missing_handlers_in_the_logger(
    loguru_logger: Logger,
):
    """Ensure PropagateHandler remove_handle doesn't fail on missing handlers."""

    assert PropagateHandler.add_handle(loguru_logger)

    with patch.object(loguru_logger, "remove") as mocked_logger_remove:
        mocked_logger_remove.side_effect = ValueError
        assert not PropagateHandler.remove_handle(loguru_logger)


def test_PropagateHandler_remove_handle_doesnt_try_to_remove_unreferenced_loggers(
    loguru_logger: Logger,
):
    """Ensure PropagateHandler remove_handles doesn't remove unreferenced loggers."""

    assert PropagateHandler.add_handle(loguru_logger)

    try:
        with patch.object(
            PropagateHandler, "_handler_reference"
        ) as mocked_handler_reference:
            mocked_handler_reference.return_value = {}

            assert not PropagateHandler.remove_handle(loguru_logger)
    finally:
        PropagateHandler.remove_handle(loguru_logger)


def test_InterceptHandler_intercepts_python_logging_for_loguru(loguru_logger: Logger):
    """Ensure InterceptHandler can intercept logs from Python's logging."""

    assert InterceptHandler.add_handle(loguru_logger)

    try:

        with patch.object(loguru_logger, "info") as mocked_info:
            logging.info("test")
            assert mocked_info.called_once_with("test")
    finally:
        assert InterceptHandler.remove_handle(loguru_logger)


def test_InterceptHandler_is_handled(loguru_logger: Logger):
    """Ensure InterceptHandler is_handled works."""

    assert not InterceptHandler.is_handled(loguru_logger)

    assert InterceptHandler.add_handle(loguru_logger)
    try:
        assert InterceptHandler.is_handled(loguru_logger)
        assert InterceptHandler.remove_handle(loguru_logger)
        assert not InterceptHandler.is_handled(loguru_logger)
    finally:
        InterceptHandler.remove_handle(loguru_logger)


def test_InterceptHandler_add_handle_doesnt_add_already_handled_logger(
    loguru_logger: Logger,
):
    """Ensure InterceptHandler add_handle doesn't re-add handled logger."""

    assert InterceptHandler.add_handle(loguru_logger)
    try:
        assert not InterceptHandler.add_handle(loguru_logger)
    finally:
        assert InterceptHandler.remove_handle(loguru_logger)


@patch("logging.basicConfig")
def test_InterceptHandler_add_handle_configures_python_logging(
    mocked_basicConfig: MagicMock, loguru_logger: Logger,
):
    """Ensure InterceptHandler add_handle configures Python logging correctly."""

    assert InterceptHandler.add_handle(loguru_logger)
    try:
        mocked_basicConfig.assert_called_once()
        _, kwargs = mocked_basicConfig.call_args
        assert "handlers" in kwargs
        assert isinstance(kwargs["handlers"], list) and len(kwargs["handlers"]) == 1
        assert isinstance(kwargs["handlers"][0], InterceptHandler.LoggingHandler)
        assert "level" in kwargs
        assert kwargs["level"] == logging.NOTSET
    finally:
        assert InterceptHandler.remove_handle(loguru_logger)


def test_InterceptHandler_remove_handle_doesnt_remove_unhandled_logger(
    loguru_logger: Logger,
):
    """Ensure InterceptHandler remove_handler doesn't remove unhandled logger."""

    assert not InterceptHandler.is_handled(loguru_logger)
    assert not InterceptHandler.remove_handle(loguru_logger)


def test_InterceptHandler_remove_handle_restores_python_logging_configuration(
    loguru_logger: Logger,
):
    """Ensure InterceptHandler remove_handler restores default Python logging config."""

    assert InterceptHandler.add_handle(loguru_logger)
    try:
        with patch("logging.basicConfig") as mocked_basicConfig:
            assert InterceptHandler.remove_handle(loguru_logger)
            mocked_basicConfig.assert_called_with(
                handlers=InterceptHandler._previous_handlers
            )
    finally:
        InterceptHandler.remove_handle(loguru_logger)


@given(
    log_record(
        level_strategy=sampled_from(list(logging._nameToLevel.values())).filter(
            lambda x: x not in (logging.NOTSET, 5)
        )
    )
)
def test_InterceptHandler_LoggingHandler_get_level_name(record: logging.LogRecord):
    """Ensure InterceptHandler's LoggingHandler gets the appropriate level name."""

    assert InterceptHandler.LoggingHandler()._get_level_name(record) == record.levelname


@given(
    log_record(level_strategy=sampled_from([logging.NOTSET, 5])),
    sampled_from(list(loguru.logger._core.levels.keys())),  # type: ignore
)
def test_InterceptHandler_LoggingHandler_get_level_name_defaults_to_given_level_name(
    record: logging.LogRecord, default_level: str
):
    """Ensure InterceptHandler's LoggingHandler gets the default level if needed."""

    assert (
        InterceptHandler.LoggingHandler()._get_level_name(
            record, default_level=default_level
        )
        == default_level
    )
