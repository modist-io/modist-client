.. _package.modist.package:

``modist.package``
==================

   The purpose of this module is to provide the functionality necessary to produce an
   archive of a given mod. This archive is a compressed
   `TAR <https://en.wikipedia.org/wiki/Tar_(computing)>`_ archive using one of the
   ``gzip``, ``bzip2``, or ``lzma`` compression strategies.

   Another custom features of theses generated archives, is the inclusion of a mod
   archive manifest which details included files and checksums for **extremely basic**
   local archive verification. These checksums are calculated, by default, using the
   `xxhash <https://cyan4973.github.io/xxHash/>`_ non-cryptographic hashing algorithm.
   Optionally, any available hashing strategy from
   :class:`~modist.package.hasher.HashType` can be used to calculate these checksums.


.. automodule:: modist.package
   :members:
   :undoc-members:
   :show-inheritance:


Archiving
---------

.. automodule:: modist.package.archive
   :members:
   :undoc-members:


Hashing
-------

.. automodule:: modist.package.hasher
   :members:
   :undoc-members:
