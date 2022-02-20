API Reference
=============

This the module index where all the models, classes and functions that make the dotmix library are documented. The CLI isn't documented but is built on top of the library using click.

.. note::
   This part of the documentation is only useful if you're planning to contribute to dotmix's development or if you're building a new tool that extends or interacts with dotmix in some way. If you only need to use dotmix, check the :doc:`usage` page

.. note::
    This page contains auto-generated API reference documentation [#f1]_.

.. toctree::
   :titlesonly:

   {% for page in pages %}
   {% if page.top_level_object and page.display %}
   {{ page.include_path }}
   {% endif %}
   {% endfor %}

.. [#f1] Created with `sphinx-autoapi <https://github.com/readthedocs/sphinx-autoapi>`_
