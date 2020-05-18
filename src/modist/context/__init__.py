# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains logic and data types for extracting info about the current context."""


from dataclasses import dataclass, field

from .modist import ModistContext
from .python import PythonContext
from .system import SystemContext


@dataclass
class Context:
    """Contains the base context properties for the current context."""

    modist: ModistContext = field(default_factory=ModistContext)
    system: SystemContext = field(default_factory=SystemContext)
    python: PythonContext = field(default_factory=PythonContext)


instance: Context = Context()

__all__ = ["instance", "Context", "ModistContext", "SystemContext", "PythonContext"]
