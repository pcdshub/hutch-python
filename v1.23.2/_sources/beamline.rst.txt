Beamline File
=============

Each hutch repository has an ``xxx/beamline.py`` file that is pointed to in
the ``conf.yml`` file. This is intended to be a place for hutches to create
hutch-specific objects or startup changes and additions. You are encouraged
to port your hutch-specific classes upstream and add the objects to the
database, but this is not necessary in every case.

The import rules for this file can be thought of as the most basic:

.. code-block:: python

   from xxx.beamline import *


This means we'll include everything in the module, unless an ``__all__`` list is
found to specify the behavior of a ``*`` import.

As specified on the `yaml_files` page, ``conf.yml`` can be extended to import
from multiple modules:

.. code-block:: YAML

   load:
     - xxx.beamline
     - xxx.my_module
