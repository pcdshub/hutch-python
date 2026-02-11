.. _object-configuration:

====================
Object Configuration
====================
``hutch-python`` allows users to customize certain aspects of objects
after instantiation.  This page will go through examples of this and
how to use these options in your own session.

An example file is provided at the bottom of this page.

Creating a configuration file
-----------------------------
Object configuration files are formatted in a simple YAML format, similar
to the conf.yml files.  The first level should be either a device name
or device class.  Note that you should not include the namespace in
these names, as ``hutch-python`` will search for the device names.
(``fast_motor1`` is ok, not ``sim.fast_motor1``)

Under this, configuration directions should be listed.

.. code-block:: YAML

    device_name:
      direction1:
        - value1

    DeviceClass:
      direction2:
        - value2



Available configuration directions
----------------------------------
Currently, ``hutch-python`` supports the following configuration directives.
If you would like to add another, please leave an
`issue <https://github.com/pcdshub/hutch-python/issues>`_ or jira ticket.

(please don't take any of these as suggested modifications)

``tab_whitelist``
^^^^^^^^^^^^^^^^^

A list of items to **reveal** in the tab-completion menu.

.. code-block:: YAML

    gon_sx:
      tab_whitelist:
        - kind


``tab_blacklist``
^^^^^^^^^^^^^^^^^

A list of items to **hide** from the tab_completion menu.  These attributes
still exist, and are simply hidden from the tab-completion menu.

.. code-block:: YAML

    at2l0:
      tab_blacklist:
        - blade_01

``replace_tablist``
^^^^^^^^^^^^^^^^^^^

A list of items to replace the tab completion list with.  This will
functionally hide all items and reveal the ones specified.

.. code-block:: YAML

    fast_motor1:
      replace_tablist:
        - position

``kind``
^^^^^^^^

Modify the ophyd ``kind`` of a device and its subcomponents.  This is
used in ophyd internals to signal if we need to "pay attention" to
a device or not.

To modify the ``kind`` of the top-level device, list the device name
and the desired ``kind`` as a key-value pair.  To modify the kind of
its components, list the component name and the desired ``kind`` as a
key-value pair.

.. code-block:: YAML

    at2l0:
      kind:
        at2l0: hinted
        blade_01: hinted
        blade_02: config


Order of Operations
-------------------
The order of the object configuration file determines the order
in which modifications are applied.  Devices/Classes are modified from
top to bottom, and the modifications are applied in the following order:

    #. tab whitelist
    #. tab blacklist
    #. replace tablist
    #. kind

Later modifications can override earlier modifications.  More explicitly,
this means that if an item is added to both the ``tab_whitelist`` and
``tab_blacklist``, it will not be shown.  Similarly the ``replace_tablist``
directive will take priority over the ``tab_blacklist`` and
``tab_whitelist`` directives.


Loading the configuration file
------------------------------
To use the configuration settings you've described, simply reference
your configuration yaml file in your ``conf.yml`` file with the
key ``obj_config``.  See :ref:`obj_conf_yaml`.

.. code-block:: YAML

    obj_config: /cds/group/pcds/pyps/apps/hutch-python/xxx/tabs.yml


Example ``obj_conf.yml``
------------------------

.. code-block:: YAML

    # Configuration options can be applied to a single device by name
    # this hides at2l0.blade_01, shows at2l0.kind, and changes the
    # kind of at2l0.blade_01 and at2l0.blade_02.
    at2l0:
      tab_whitelist:
        - kind
      tab_blacklist:
        - blade_01
      kind:
        blade_01: hinted
        blade_02: config

    # or to all devices of a specific class
    pcdsdevices.epics_motor.IMS:
      tab_whitelist:
        - kind

    # This tries to limit the tab completion list to only `kind`
    FastMotor:
      replace_tablist:
        - kind

    # This will allow `limits` to be seen in specifically `fast_motor1`
    # while other simulated fast motors will only see `kind`
    fast_motor1:
      tab_whitelist:
        - limits
