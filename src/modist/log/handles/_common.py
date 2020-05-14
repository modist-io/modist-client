# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains the common base class log handlers should inherit from."""

import abc

from loguru._logger import Logger


class BaseLogHandler(abc.ABC):
    """The abstract handler interface for how log handlers should be built."""

    @abc.abstractclassmethod
    def is_handled(self, logger: Logger) -> bool:
        """Quick helper method to check if the given logger is already being handled.

        :param Logger logger: The logger to check if already handled
        :return: True if the logger is already handled, otherwise False
        :rtype: bool
        """

        raise NotImplementedError()

    @abc.abstractclassmethod
    def add_handle(self, logger: Logger) -> bool:
        """Add the logging handler to the given logger instance.

        :param Logger logger: The logger instance to add the handler to
        :return: True if the handler was added, False if the handle was already present
        :rtype: bool
        """

        raise NotImplementedError()

    @abc.abstractclassmethod
    def remove_handle(self, logger: Logger) -> bool:
        """Remove the logging handler from the given logger instance.

        :param Logger logger: The logger instance to remove the handle
        :return: True if the handler was removed, False if there was no handler present
        :rtype: bool
        """

        raise NotImplementedError()
