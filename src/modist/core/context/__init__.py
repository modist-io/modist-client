# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""
"""

from dataclasses import dataclass, field

from .python import PythonContext
from .system import SystemContext


@dataclass
class Context:

    system: SystemContext = field(default_factory=SystemContext)
    python: PythonContext = field(default_factory=PythonContext)


instance: Context = Context()

__all__ = ["instance", "Context", "SystemContext", "PythonContext"]
