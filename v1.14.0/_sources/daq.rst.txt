DAQ
===

The following objects are provided for interacting with the data acquisition
system:

    - ``daq``: controls execution of the run
    - ``scan_pvs``: controls the auxilliary scan pvs, which are used to
      organize the run tables.

Full documentation is available at `<https://pcdshub.github.io/pcdsdaq>`_.
This page will be a brief overview.

.. note::

   ``scan_pvs`` are disabled by default! This is to prevent confusion from
   two users accidentally writing to the PVs at the same time. Call
   ``scan_pvs.enable()`` to enable them. You may consider doing this as part
   of your standard scan routine.


Basic Usage
-----------

Use ``daq.begin`` to start a run. Runs must be ended explicitly or the
run will remain open. A second call to a begin during an open run will
resume the run.

.. ipython:: python
   :suppress:

   from bluesky.run_engine import RunEngine
   from bluesky.plans import scan
   from ophyd.sim import motor
   from pcdsdaq.daq import Daq
   from pcdsdaq.sim import set_sim_mode

   set_sim_mode(True)
   RE = RunEngine({})
   daq = Daq(RE=RE)

.. ipython:: python

   # Run for 120 events, wait, leave the run open.
   daq.begin(events=120, wait=True)
   # Close the run
   daq.end_run()
   # Run for 1 second, record, set the run to end automatically
   daq.begin(duration=1, record=True, end_run=True)
   # Wait until done taking data
   daq.wait()

The python will steal control from the GUI. Only one or the other can have
control at a time. Use ``daq.disconnect`` to give up control to the GUI.

.. ipython:: python

   daq.disconnect()

You can start an infinite run using ``daq.begin_infinite``. You can stop this
run manually using ``daq.end_run``.


In a Scan
---------

Use the ``daq`` object as your detector to include it in a ``bluesky`` plan.
The ``DAQ`` will then run for the configured duration at every scan step.
If ``scan_pvs`` are enabled, these will be written to during the ``bluesky``
plan.

.. ipython:: python

   # Configure for 120 events per point
   daq.preconfig(events=120)
   # Scan motor from 0 to 10 in 11 steps, run daq at each point
   RE(scan([daq], motor, 0, 10, 11))


Controlling Post-Scan State
---------------------------

The daq will return to the state it was in before the scan was run. If we
start disconnected, we will revert to disconnected. If we start configured,
we will stay connected and configured. If we start while already running,
we'll start running again (``record=False``) after the scan.

The ``daq.configure`` method must connect, so the ``daq.preconfig``
method is provided if you'd like to schedule a configuration to apply
upon connecting in the scan.
