# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains logic and data types for extracting info about the Python runtime."""

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
    IronPython = "ironpython"
    Jython = "jython"
    PyPy = "pypy"


def get_implementation() -> Optional[PythonImplementation]:
    """Determine teh current Python implementation.

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

    :return: The :class:`pathlib.Path` instance to the current Python path if found
    :rtype: Optional[pathlib.Path]
    """

    path_entry = PythonFinder().which("python")
    if not path_entry:
        return None

    return path_entry.path


@dataclass
class PythonContext:
    """Contains the context properties of the current Python runtime."""

    path: Optional[Path] = field(default_factory=get_path)
    version: Version = field(default_factory=get_version)
    implementation: Optional[PythonImplementation] = field(
        default_factory=get_implementation
    )
