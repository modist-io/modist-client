.. _package.modist.log:

``modist.log``
==============

.. automodule:: modist.log
   :members:
   :undoc-members:
   :show-inheritance:


Log Captures
------------

   Sometimes we need to silently capture events and log messages out to whatever output
   sinks have been defined. Some examples of this would be capturing all uncaught
   exceptions as log errors or Python warnings as log warnings.

   The following module provides a namespace for custom event capturing logic.

.. automodule:: modist.log.captures
   :members:


Python Warnings
'''''''''''''''

.. automodule:: modist.log.captures.python_warnings
   :members:


Python Exceptions
'''''''''''''''''

.. automodule:: modist.log.captures.python_exceptions
   :members:


Log Handlers
------------

   Sometimes it's necessary to add custom handler logic for log records to either
   pass the log into other sinks or do some additional handling / processing of the log
   before it makes it to output sinks.

   This module provides a namespace for custom logging handlers.

.. automodule:: modist.log.handles
   :members:

Python Logging
''''''''''''''

.. automodule:: modist.log.handles.python_logging
   :members:


Log Patchers
------------

   Occasionally we will have the need to patch a logger to always include some kind of
   information. This is typically done through Loguru's
   :meth:`~loguru._logger.Logger.patch` function which returns a wrapped logger and will
   always include whatever changes are applied as part of that patcher.

   We have made the following module to have a namespace where we can keep all of our
   defined logging patchers. We also supply some helper methods to make the syntax of
   applying patchers consistent across whatever usage we need.


.. automodule:: modist.log.patchers
   :members:
