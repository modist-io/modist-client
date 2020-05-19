.. _modist:

Package Documentation
=====================

The module that exposes mostly all of the package's functionality.

.. automodule:: modist
   :members:
   :undoc-members:
   :show-inheritance:


:mod:`modist.core`
------------------

Provides core data models and functionality.

.. code-block:: python

   from modist.core import Mod
   mod = Mod.from_dir(Path("/home/mickey/Downloads/my-mod/"))


:mod:`modist.context`
---------------------

Provides data structures to standardize how the runtime's context is collected.

.. code-block:: python

   from modist.context import instance as ctx
   ctx.modist.version
   ctx.system.is_64bit
   ctx.python.path


:mod:`modist.log`
-----------------

Provides pre-configured client logging instances.

.. code-block:: python

   from modist.log import instance as log
   log.info("Hello, world!")


:mod:`modist.exceptions`
------------------------

Contains custom exceptions used throughout the client module

.. code-block:: python

   from modist.exceptions import NotAMod
   raise NotAMod("The provided instance is not a valid mod")
