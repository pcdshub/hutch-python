Useful Utilities
================

The ``hutch_python.utils`` and ``hutch_python.namespace`` modules have
functions that may be broadly useful.

`hutch_python.utils.safe_load` can be used as a shortcut for wrapping code
that may or may not succeed to prevent a bad submodule from interrupting the
``hutch-python`` load sequence. This means that if the ``Attenuator`` class is
bugging out, we'll be warned that there is a problem and skip it, but you'll
still be able to manipulate the ``Slits`` objects.

For example, this will complete successfully but show a warning:

.. ipython:: python

    from hutch_python.utils import safe_load

    with safe_load('divide by zero'):
        1/0


The reason for the failure with the full traceback will be saved to the log
file and will be visible in the terminal if you are in `debug mode <debug>`.

`hutch_python.namespace.class_namespace` can be used to create your own object
groupings by type. This will find all objects loaded by hutch python plus all
objects in your global environment, and accumulate them if they match a given
type. You can explititly provide the type object or you can opt to provide a
string.

.. code-block:: python

    from hutch_python.namespace import class_namespace

    one = 1
    two = 2
    three = 3

    integers = class_namespace(int)


.. ipython:: python
    :suppress:

    from hutch_python.namespace import class_namespace

    one = 1
    two = 2
    three = 3

    integers = class_namespace(int)

.. ipython:: python

    integers.three
    list(integers)  # Iterate through namespace in alphabetical order
