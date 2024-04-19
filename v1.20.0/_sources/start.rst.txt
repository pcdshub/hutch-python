Starting a Session
==================

Quick-start
-----------

Run the ``xxxpython`` script in hutch ``xxx``'s directory to start a session.
You do not need a specific ``python`` environment to do this.

Hutch Directories
-----------------

Each hutch has its own ``hutch-python`` landing directory that facilitates
launching a session. You should use the central directory at
``/reg/g/pcds/pyps/apps/hutch-python/xxx`` if you are running an
experiment. This is a clone of the central
``https://github.com/pcdshub/xxx`` repository. You have the option to
clone this for debugging and development.

You do not need to have a ``Python`` environment set up to run out of this
landing directory. All of the environment configuration is done for you in the
launch scripts.

There is a launch script and an environment script:

- ``xxxpython``: Main launch script.
                 Starts an ``ipython`` session with hutch's environment and
                 configured devices. If called with a script, runs that script
                 instead of starting an interactive session. This feature is
                 useful for scripts that need to rely on the hutch's configured
                 devices.
- ``xxxenv``: Environment setup script.
              Source this script to activate the hutch's ``python``
              environment without running any particular script.


Command Line Options
--------------------

There are three additional options to ``xxxpython`` that may be useful.

- ``xxxpython --exp <expname>``: Override the active experiment for a single
                                 session. This is useful for setup and testing.
- ``xxxpython --sim``: Start the session with a simulated ``Daq`` object.
                       This may be useful to test scans that need the daq when
                       the daq is unavailable.
- ``xxxpython --debug``: Start the session in debug mode.
                         This will greatly increase the number of ``logger``
                         messages that are displayed in the terminal. See
                         `debug` more more information.

These arguments may be used at the same time e.g. ``xxxpython --sim --debug``.
