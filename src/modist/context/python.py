# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Module that contains logic and factory methods for buiding the Python context."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from platform import python_implementation, python_version
from typing import Optional

from pythonfinder import Finder as PythonFinder
from semantic_version import Version


class PythonImplementation(Enum):
    """Enumeration of suported Python implementations."""

    CPython = "cpython"
    """Indicates a CPython (base Python) runtime. """

    IronPython = "ironpython"
    """Indicates an IronPython (.NET) runtime."""

    Jython = "jython"
    """Indicates a Jython (Java VM) runtime."""

    PyPy = "pypy"
    """Indicates a PyPy (JIT CPython) runtime."""


def get_implementation() -> Optional[PythonImplementation]:
    """Determine the current Python implementation.

    :return: The appropriate :class:`~PythonImplementation` instance if found
    :rtype: Optional[PythonImplementation]
    """

    try:
        return PythonImplementation(python_implementation().lower())
    except ValueError:
        return None


def get_version() -> Version:
    """Determine the current Python approximate version.

    :return: The approximate :class:`~semantic_version.Version` instance for the current
        Python release version
    :rtype: ~semantic_version.Version
    """

    return Version.coerce(python_version())


def get_path() -> Optional[Path]:
    """Determine the current Python runtime path.

    :return: The :class:`~pathlib.Path` instance to the current Python path if found
    :rtype: Optional[~pathlib.Path]
    """

    path_entry = PythonFinder().which("python")
    if not path_entry:
        return None

    return path_entry.path


@dataclass
class PythonContext:
    """Dataclass that contains the Python-specific context details.

    >>> from modist.context.python import PythonContext
    >>> ctx = PythonContext()
    ctx.version

    :param Optional[~pathlib.Path] path: The path to the current Python executable
    :param ~semantic_version.Version version: The coerced semantic version of the
        active Python runtime
    :param Optional[PythonImplementation] implementation: The current implementation
        of the active Python runtime
    """

    path: Optional[Path] = field(default_factory=get_path)
    version: Version = field(default_factory=get_version)
    implementation: Optional[PythonImplementation] = field(
        default_factory=get_implementation
    )
