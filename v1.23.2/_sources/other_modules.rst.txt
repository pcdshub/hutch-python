Related Modules
===============

Here are some links to documentation of modules that ``hutch-python`` relies
heavily on:

- SLAC Modules:

  - `pcdsdaq <https://pcdshub.github.io/pcdsdaq>`_: For using the daq
        These documents explain how to use the ``daq`` object and how to
        incorporate the ``daq`` object into ``bluesky`` plans.
  - `pcdsdevices <https://pcdshub.github.io/pcdsdevices>`_: For LCLS devices
        These documents are a complete API specification for available device
        classes, along with an explanation of some of the more important
        interfaces.
  - `happi <https://pcdshub.github.io/happi>`_: For object loading
        These documents show how to add devices to the shared database, and
        how to read them back.

- NSLS-II Modules:

  - `bluesky <https://nsls-ii.github.io/bluesky>`_: For using the ``RunEngine``
        These documents explain how to create and use ``plans`` and how to use
        the ``RE`` object to run them. It also goes into depth about how the
        ``RunEngine`` works and how it can be customized.
  - `ophyd <https://nsls-ii.github.io/ophyd>`_: For developing LCLS devices
        These documents describe the design philosophy behind the ``ophyd``
        ``Device`` architecture and how to create new device classes.
