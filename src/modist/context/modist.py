# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Module that contains logic and factory methods for building the Modist context."""

from dataclasses import dataclass, field

from semantic_version import Version

from ..__version__ import __author__, __contact__, __version__


def get_name() -> str:
    """Determine the name of the Modist client's context.

    :return: The name of the client's context
    :rtype: str
    """

    return "Modist"


def get_author() -> str:
    """Determine the author strubg of the Modist client.

    :return: The author string of the Modist client
    :rtype: str
    """

    return __author__


def get_contact() -> str:
    """Determine contact details for the Modist client.

    :return: The contact details of the Modist client
    :rtype: str
    """

    return __contact__


def get_version() -> Version:
    """Determine the version of the Modist client.

    :return: The appropraite :class:`~semantic_version.Version` of the Modist client
    :rtype: ~semantic_version.Version
    """

    return Version(__version__)


@dataclass
class ModistContext:
    """Dataclass that contains the Modist-specific context details.

    Initializing this class with no parameters will dynamically resolve the parameters
    using the included factory methods just as the base
    :class:`~modist.context.Context` dataclass does.

    >>> from modist.context.modist import ModistContext
    >>> ctx = ModistContext()
    ctx.name

    .. important:: Overriding the defaults produced from just instantiating this class
        is highly discouraged. Many of these details are needed for producing system
        configuration directories and may cause errors down the line if overridden
        during runtime.

        I would recommend you never initialize this class yourself and instead rely on
        the :data:`~modist.context.instance` provided by :mod:`modist.context`.

    :param str name: Explicitly ``Modist``
    :param str author: The included author string of the client package
    :param str contact: The included contact string of the client package
    :param ~semantic_version.Version version: The semantic version of the client package
    """

    name: str = field(default_factory=get_name)
    author: str = field(default_factory=get_author)
    contact: str = field(default_factory=get_contact)
    version: Version = field(default_factory=get_version)
