# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""
"""

from dataclasses import dataclass, field
from enum import Enum
from platform import python_implementation, python_version
from typing import Optional

from semantic_version import Version


class PythonImplementation(Enum):

    CPython = "cpython"
    IronPython = "ironpython"
    Jython = "jython"
    PyPy = "pypy"


def get_implementation() -> Optional[PythonImplementation]:
    try:
        return PythonImplementation(python_implementation().lower())
    except ValueError:
        return None


def get_version() -> Version:
    return Version.coerce(python_version())


@dataclass
class PythonContext:

    version: Version = field(default_factory=get_version)
    implementation: Optional[PythonImplementation] = field(
        default_factory=get_implementation
    )
