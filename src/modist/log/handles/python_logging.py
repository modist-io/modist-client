# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Loguru handles for Python's builtin logging."""

import copy
import logging
from functools import lru_cache
from typing import Any, Dict, List, Optional

import loguru
from loguru._logger import Logger

from ._common import BaseLogHandler


class PropagateHandler(BaseLogHandler):
    """Propagate Loguru's logging records to Python's builtin logging."""

    _handler_reference: Dict[Any, int] = {}

    class LoggingHandler(logging.Handler):
        """Log handler that propagates Loguru logs to Python's builtin logging."""

        def handle(self, record: logging.LogRecord):
            """Given a :class:`logging.LogRecord` from Loguru, handle it with Python logging.

            :param logging.LogRecord record: The log record to handle
            """

            logging.getLogger(record.name).handle(record)

    @staticmethod
    def _get_config() -> Dict[str, Any]:
        """Get the loguru configuration dictionary that should be used for this handler.

        :return: The configuration dictionary to add to loguru's logger, or None
        :rtype: Dict[str, Any]
        """

        return dict(
            sink=PropagateHandler.LoggingHandler(level=logging.DEBUG),
            format="{message}",
        )

    @classmethod
    def _get_handler_id(cls, logger: Logger) -> Optional[int]:
        """Get the handler's id for the given logger.

        :param Logger logger: The logger to lookup the handler id for
        :return: The integer id of the given logger's handler, otherwise None
        :rtype: Optional[int]
        """

        if logger in cls._handler_reference:
            return cls._handler_reference[logger]

        return None

    @classmethod
    def is_handled(cls, logger: Logger) -> bool:
        """Quick helper method to check if the given logger is already being handled.

        :param Logger logger: The logger to check if already handled
        :return: True if the logger is already handled, otherwise False
        :rtype: bool
        """

        return cls._get_handler_id(logger) is not None

    @classmethod
    def add_handle(cls, logger: Logger) -> bool:
        """Add the logging handler to the given logger instance.

        :param Logger logger: The logger instance to add the handler to
        :return: True if the handler was added, False if the handle was already present
        :rtype: bool
        """

        if cls.is_handled(logger):
            return False

        handler_id: int = logger.add(**PropagateHandler._get_config())
        cls._handler_reference[logger] = handler_id

        return True

    @classmethod
    def remove_handle(cls, logger: Logger) -> bool:
        """Remove the logging handler from the given logger instance.

        :param Logger logger: The logger instance to remove the handle
        :return: True if the handler was removed, False if there was no handler present
        :rtype: bool
        """

        if not cls.is_handled(logger):
            return False

        handler_id = cls._get_handler_id(logger)
        try:
            if not handler_id:
                return False

            logger.remove(handler_id)
            return True
        except ValueError:
            # NOTE: this occurs in an edge-case where the logger is intialized and a
            # PropagateHandler.Logginghandler is added manually
            # (not using the included methods).
            # This doesn't really cause any issues in normal execution, just that the
            # `handler_id` won't exist in our references. Another reason to only
            # configure the loguru logger only once at startup and avoid doing
            # subsequent calls to `modist.log.configure_logger`.
            return False
        finally:
            if logger in cls._handler_reference:
                del cls._handler_reference[logger]


class InterceptHandler(BaseLogHandler):
    """Intercept Python's builtin logging as Loguru logging records.

    .. important:: Python log intercepting is not very robust or dynamic. You bascially
        need to decided if you want to intercept all logs or if you want to ignore other
        module's log's at the very start of runtime. You can't update constructed
        loggers from Python's builtin :mod:`logging` after they have been defined.

        Also any third-party module that calls :func:`logging.basicConfig` and resets
        global logging handlers will break this handler. Your best course of action is
        to just accept that Python's logging will always suck and only worry about your
        own modules logging.
    """

    _is_intercepting: bool = False
    _previous_handlers: List[Any] = []

    class LoggingHandler(logging.Handler):
        """Log handler that intercepts Python's builtin logging for Loguru logs."""

        @lru_cache()
        def _get_level_name(
            self, record: logging.LogRecord, default_level: str = "INFO"
        ) -> str:
            """Determine the loguru record name for the given Python logging record.

            :param logging.LogRecord record: The record to determine the level name from
            :return: The logging level name for Loguru
            :rtype: str
            """

            valid_names = list(loguru.logger._core.levels.keys())  # type: ignore
            if record.levelname in valid_names:
                return record.levelname

            return default_level

        def emit(self, record: logging.LogRecord):  # pragma: no cover
            """Given a :class:`logging.LogRecord` from logging, handle it with Loguru logging.

            :param logging.LogRecord record: The log record to handle
            """

            frame, depth = logging.currentframe(), 2  # type: ignore
            while frame.f_code.co_filename == logging.__file__:
                if frame.f_back is not None:
                    frame = frame.f_back
                depth += 1

            loguru.logger.opt(depth=depth, exception=record.exc_info).log(
                self._get_level_name(record), record.getMessage()
            )

    @classmethod
    def is_handled(cls, logger: Logger) -> bool:
        """Quick helper method to check if the given logger is already being handled.

        :param Logger logger: The logger to check if already handled
        :return: True if the logger is already handled, otherwise False
        :rtype: bool
        """

        return cls._is_intercepting

    @classmethod
    def add_handle(cls, logger: Logger) -> bool:
        """Add the logging handler to the given logger instance.

        :param Logger logger: The logger instance to add the handler to
        :return: True if the handler was added, False if the handle was already present
        :rtype: bool
        """

        if cls.is_handled(logger):
            return False

        cls._previous_handlers = copy.copy(logging._handlerList)  # type: ignore
        logging.basicConfig(handlers=[cls.LoggingHandler()], level=logging.NOTSET)
        cls._is_intercepting = True
        return True

    @classmethod
    def remove_handle(cls, logger: Logger) -> bool:
        """Remove the logging handler from the given logger instance.

        :param Logger logger: The logger instance to remove the handle
        :return: True if the handler was removed, False if there was no handler present
        :rtype: bool
        """

        if not cls.is_handled(logger):
            return False

        logging.basicConfig(handlers=cls._previous_handlers)
        cls._is_intercepting = False
        return True
