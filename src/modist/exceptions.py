# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Custom module-wide exceptions."""


class ModistException(Exception):
    """Base module-wide exception namespace.

    .. note:: To easily except all custom module exceptions, you can simply catch
        this exception as all custom exceptions inherit from this.
    """

    def __init__(self, message: str):
        """Initialize the exception instance.

        :param str message: The message of the exception
        """

        self.message = message
        super().__init__(message)


class IsAMod(ModistException):
    """Indicates the building of a mod failed to a mod already exsisting."""


class NotAMod(ModistException):
    """Indicates the building of a mod failed due to given information being invalid."""


class NotAnArchive(ModistException):
    """Indicates a provided reference is not a valid archive."""


class BadArchive(ModistException):
    """Indicates something went wrong when evaluating an archive."""
