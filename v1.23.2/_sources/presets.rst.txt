=======
Presets
=======
``hutch-python`` provides a position presets system through the
``pcdsdevices`` module. See the
`presets documentation <https://pcdshub.github.io/pcdsdevices/presets.html>`_
for a full description. On this page we will go through examples
and show where the presets are stored.


Example Usage
-------------

Creating a permenant preset named ``tt`` for a motor named ``reflaser``:

.. code-block:: python

   reflaser.presets.add_hutch('tt', 42.1, comment='Add timetool in pos')

Move to a preset, and check that we got there:

.. ipython::
   :verbatim:

   # Check where we are
   In [1]: reflaser.wm()
   Out[1]: 10.0

   In [1]: reflaser.wm_tt()
   Out[1]: 32.1

   # Do the move and wait
   In [1]: reflaser.mv_tt(wait=True)

   # Check where we ended up
   In [1]: reflaser.wm()
   Out[1]: 42.1

   In [1]: reflaser.wm_tt()
   Out[1]: 0.0

Two ways to revise a position:

.. code-block:: python

   reflaser.presets.add_hutch('tt', 41.2, comment='Fix timetool pos')
   reflaser.presets.positions.tt.update_pos(40.0, comment='Fix it again')

Create a single-experiment preset named ``sample`` for a motor ``gon_x``
at the current position:

.. code-block:: python

   gon_x.presets_add_exp_here('sample', comment='Sample pos shift 1')

Accidentally misspell a preset name, and then remove it:

.. code-block:: python

   gon_y.presets.add_exp_here('smlp', comment='Sample pos shift 1')
   gon_y.presets.positions.smlp.deactivate()

Check all of the active presets:

.. ipython::
   :verbatim:

   In [1]: reflaser.presets.positions
   Out[1]: namespace(refl=20.0, tt=40.0)

Check the history of a single preset:

.. ipython::
   :verbatim:

   In [1]: reflaser.presets.tt.history
   Out[1]: {'23 Apr 2018 10:37:49': '   42.1000 Add timetool in pos',
            '23 Apr 2018 10:38:00': '   41.2000 Fix timetool pos',
            '23 Apr 2018 10:39:00': '   40.0000 Fix it again'}


Preset Files
------------
The presets are stored in yaml files inside of the hutch python app directory
e.g. ``/reg/g/pcds/pyps/apps/hutch-python/mfx``, or in your checkout if
doing development. Inside this directory we have a ``presets`` directory.
Inside that directory we have a ``beamline`` directory for the permanent
presets, and a separate directory for each experiment.

.. code-block:: bash

   $ cd /reg/g/pcds/pyps/apps/hutch-python/mfx/presets
   $ ls
   05516  beamline  ls4916

The files have the name of the particular motor e.g. ``reflaser.yml``. They are
structured in a readable yaml format, like so:

.. code-block:: yaml

   refl:
     active: true
     history:
       23 Apr 2018 11:00:00: '   20.0000 Add reflaser in pos'
     value: 20.0
   tt:
     active: true
     history:
       23 Apr 2018 10:37:49: '   42.1000 Add timetool in pos'
       23 Apr 2018 10:38:00: '   41.2000 Fix timetool pos'
       23 Apr 2018 10:39:00: '   40.0000 Fix it again'
     value: 40.0

You are free to edit these by hand if you maintain the format.
