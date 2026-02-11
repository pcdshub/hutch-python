Experiment File
===============

Each hutch repository has an ``experiments`` directory for storing
experiment-specific code. To have the ``hutch-python`` loader automatically
pick up your experiment's code, you will need to follow some conventions.

An experiment name will be something like ``xppls2516`` which is composed of
the hutch ``xpp``, the proposal ``ls25``, and the run ``16``. Hutch python is
looking for a file named ``experiments/ls2516.py``, which is simply the
proposal name and the run concatenated, all lowercase.

The import rules for this file can be thought of as:

.. code-block:: python

   from experiments.ls2516 import User
   user = User()
   x = user


So, you are expected to organize your experiment-specific objects, plans, and
macros into a cohesive ``User`` class.

If your ``conf.yml`` file does not include an ``experiment`` specification,
the current experiment is picked up automatically. If you want to use an
experiment other than the current experiment, you can override this as:

.. code-block:: YAML

   experiment:
     proposal: ls25
     run: 16


See `yaml_files` for more information.

You can also override for a single session with a command-line argument:

.. code-block:: bash

   hutch-python --exp ls2516


Questionnaire
-------------

The CDS section of the questionnaire is read by ``hutch-python``, and objects
with defined python names are created. Links to the questionnaire for each run
can be found at `<https://pswww.slac.stanford.edu>`_.

These questionnaire objects will make it into the main namespace like all the
other objects, and will also be attached to the ``User()`` object.
