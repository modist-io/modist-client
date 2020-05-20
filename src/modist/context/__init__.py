# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Module that contains logic and data types for the full client context.

Although you can do many tricks with the supplied classes and methods, 99% of usage of
this module should look **exactly** like the following:

>>> from modist.context import instance as ctx
>>> ctx.system.is_64bit
True
"""


from dataclasses import dataclass, field

from .modist import ModistContext
from .python import PythonContext
from .system import SystemContext


@dataclass
class Context:
    """Dataclass that contains the full client context.

    Initializing this class with no parameters will result in class attributes being
    constructed via factory callables. In this case the factory callables are the other
    "sub-context" classes such as :class:`~.modist.ModistContext` and
    :class:`~.system.SystemContext` as they will perform similar dynamic instance
    construction.

    >>> from modist.context import Context, ModistContext
    >>> ctx = Context()
    >>> assert isinstance(ctx.modist, ModistContext)
    >>> ctx.modist.name

    If you wish to override a specific field within the constructed context instance,
    make sure you supply the necessary instances for the overriden parameters. Because
    these classes dynamically construct themselves with any missing parameters, you can
    get somewhat specific in what you want to override.

    >>> from modist.context import Context, ModistContext
    >>> ctx = Context(modist=ModistContext(name="My Name"))
    >>> assert ctx.modist.name == "My Name"

    :param ModistContext modist: An initialized Modist context instance
    :param SystemContext system: An initialized system context instance
    :param PythonContext python: An initialized Python context instance
    """

    modist: ModistContext = field(default_factory=ModistContext)
    system: SystemContext = field(default_factory=SystemContext)
    python: PythonContext = field(default_factory=PythonContext)


instance: Context = Context()
"""Globally available instance of the full client context.

Typically, in cases where you need the context instance you should be using this
variable. Continually building instances of :class:`Context` is not really a bad thing
but should be avoided as it *might* have side-effects.

The usage I would recommend is the following:

>>> from modist.context import instance as ctx
>>> ctx.system.is_64bit
True

:type: Context
"""

__all__ = ["instance", "Context", "ModistContext", "SystemContext", "PythonContext"]
