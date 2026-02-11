Startup Sequence
================

Calling ``xxxpython`` is an alias for calling ``hutch-python --cfg cfg.yml``.
The ``cfg.yml`` file defines what the loader will do. The specifics of this
file are documented on the `yaml files <yaml_files>` page.

Each step of the startup can freely access any objects defined by previous
steps. In order, the startup sequence is as follows:

- Common Startup

  - Set up log files, debug state, and sim state
  - Read ``cfg.yml``
  - Display the ``xxxpython`` banner
  - Create and set up a ``RunEngine`` as ``RE``
  - Create the ``plans`` object with default plans and alias to ``p``
  - Create the ``daq`` object
  - Create the ``scan_pvs`` object

- `Database <database>` Load

  - Load the ``db`` from ``cfg.yaml`` using ``happi``
  - Create the ``xxx_beampath`` object using ``lightpath``
  - Create cameras using the camviewer configuration file

- `Beamline <beamline>` Load

  - Import all objects from the modules under ``load`` in ``cfg.yaml``.
    By convention, this is just ``xxx.beamline``, but it can also be extended
    to a list of modules.

- `Experiment <experiment>` Load

  - Automatically select the hutch's current experiment if one was not
    provided in the ``cfg.yml``.
  - Create user objects from the experiment questionnaire
    using ``happi`` and ``psdm_qs_cli``.
  - Import ``User`` class from experiment file and instantiate ``User()``.
  - Attach all questionnaire objects to the ``User()`` object
  - If there was no experiment file, make a ``SimpleNamespace()`` object
    instead
  - Set this object to be ``x`` and ``user``.

- Groups Load

  - If any ``EpicsMotor`` objects were defined previously, group them into a
    ``motors`` object. Alias this to ``m``.
  - If any ``Slits`` objects were defined previously, group them into a
    ``slits`` object. Alias this to ``s``.
  - Group all loaded objects by metadata, to be found in a tab-accessible way
    e.g. ``xxx.dg1.name``
  - Group everything into an ``all_objects`` object. Alias this to ``a``.

- Finish

  - Create all ``_debug`` objects as documented on the `debug <debug>` page.
  - Enable input, output, and error logger
  - Enter the ``ipython`` terminal
