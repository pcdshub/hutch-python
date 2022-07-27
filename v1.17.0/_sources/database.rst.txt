Database Objects
================

Database objects are objects that are loaded from the shared device database.
This has the advantage of allowing us to have consistent devices across
different hutches and it reduces clutter in the `beamline <beamline>` file.

After loading a ``hutch-python`` session, a file is created at ``xxx/db.txt``
detailing every device that was loaded, in the order they were loaded.
This file has no function, but it serves as rough guide for understanding
which objects the database is providing.

All database objects can be found in a special module called ``xxx.db`` that
is created at runtime. This will work like a normal module you can import
from:

.. code-block:: python

    from bluesky.plans import scan
    from mfx.db import RE, mfx_attenuator

    RE(scan([], mfx_attenuator, 0, 1, 10))


This can be used to bring database or `beamline <beamline>` objects into the
`experiment <experiment>` file.
