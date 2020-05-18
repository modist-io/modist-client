# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains logic and data types for extracting info about the Modist client."""

from dataclasses import dataclass, field

from semantic_version import Version

from ..__version__ import __author__, __contact__, __version__


def get_name() -> str:
    """Determine the name of the Modist context.

    :return: The name of the Modist context
    :rtype: str
    """

    return "Modist"


def get_author() -> str:
    """Determine the author of the Modist application.

    :return: The name of the Modist application
    :rtype: str
    """

    return __author__


def get_contact() -> str:
    """Determine contact details for the Modist application.

    :return: The contact details of the Modist application
    :rtype: str
    """

    return __contact__


def get_version() -> Version:
    """Determine the version of the Modist client.

    :return: The appropraite :class:`~semantic_version.Version` of the Modist client
    :rtype: Version
    """

    return Version(__version__)


@dataclass
class ModistContext:
    """Contains the context properties of the current Modist client."""

    name: str = field(default_factory=get_name)
    author: str = field(default_factory=get_author)
    contact: str = field(default_factory=get_contact)
    version: Version = field(default_factory=get_version)
