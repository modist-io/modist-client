.. _package.modist.context:

``modist.context``
==================

   The purpose of this module is to provide a standard way of accessing identifying
   information about the current client's runtime.

   Typically when dealing with applications that need to be cross-os-compatable we take
   drastic measures to fetch specific identifying features of the runtime's context. This
   over-usage of calls to :func:`platform.system` or :data:`sys.version_info` causes us
   to lose track of how this information is collected or shared between modules.

   By providing standardized :func:`~dataclasses.dataclass` classes accompanied with
   one-off methods for getting specific context information, we can reduce the amount of
   scatter that usually occurs with cross-compatable modules.

.. automodule:: modist.context

----

.. autoclass:: modist.context.Context
   :members:

.. autodata:: modist.context.instance
   :annotation:


Modist Context
--------------

   The Modist context contains basic information about the current client. Details such
   as :data:`~ModistContext.name` and :data:`~ModistContext.version` are useful for
   error traces, conditional validation, user visible details, etc.

.. automodule:: modist.context.modist
   :members:


System Context
--------------

   The system context contains details about the current runtime's host system. This
   information is typically going to be used for making decisions for
   cross-os-compatable logic. Some of this information is quite useful for slight
   optimizations in the runtime such as our use-case of the
   :data:`~SystemContext.is_64bit` attribute in :mod:`modist.package.hasher`.

.. automodule:: modist.context.system
   :members:


Python Context
--------------

   The Python context contains details about the current Python runtime. This
   information is mostly used for determining the source of errors or providing helpful
   traceback details to logged exceptions. These details are also useful for providing
   information to the user when trying to debug issues.

.. automodule:: modist.context.python
   :members:

