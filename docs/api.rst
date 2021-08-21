===
API
===

This is the reference for all the models, classes and functions that make the dttr library. The CLI is built on top this using click.

.. note::
   This document is only useful if you're planning to contribute to dttr's development or are if you're building new piece of software that extends or interacts with dttr in some way. If you only need to use dttr, check the :doc:`usage` page


.. contents:: :local:

*************
Configuration
*************

.. automodule:: dttr.config
   :members:
   :undoc-members:


************
Data
************

Base Data Classes
=================

Abstract Data Class
-------------------
.. autoclass:: dttr.data.AbstractData
   :members:
   :undoc-members:
   :private-members:

Basic Data Class
----------------
.. autoclass:: dttr.data.BasicData
   :members:
   :undoc-members:
   :inherited-members:
   :show-inheritance:


Base data functions
===================
.. automodule:: dttr.data
   :members:
   :undoc-members:
   :exclude-members: AbstractData,BasicData,DataFileMetadata,DataFileModel



Concrete Data Classes
=====================

Fileset
-------
.. autoclass:: dttr.fileset.Fileset
   :members:
   :undoc-members:
   :inherited-members:
   :show-inheritance:

.. automodule:: dttr.fileset
    :members:
    :undoc-members:
    :exclude-members: Fileset

Appearance
----------
.. autoclass:: dttr.appearance.Appearance
   :members:
   :undoc-members:
   :inherited-members:
   :show-inheritance:

.. automodule:: dttr.appearance
    :members:
    :undoc-members:
    :exclude-members: Appearance


Colorscheme
-----------
.. autoclass:: dttr.colorscheme.Colorscheme
   :members:
   :undoc-members:
   :inherited-members:
   :show-inheritance:

.. automodule:: dttr.colorscheme
    :members:
    :undoc-members:
    :exclude-members: Colorscheme



Typography
----------
.. autoclass:: dttr.typography.Typography
   :members:
   :undoc-members:
   :inherited-members:
   :show-inheritance:

.. automodule:: dttr.typography
    :members:
    :undoc-members:
    :exclude-members: Typography


******
Runner
******

.. automodule:: dttr.runner
    :members:
    :undoc-members:


*********
Utilities
*********

General
=======
.. automodule:: dttr.utils
   :members:
   :undoc-members:


Color utilities
===============
.. automodule:: dttr.colorscheme.utils
   :members:
   :undoc-members:
