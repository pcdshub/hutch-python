Environments
============

Central Install
---------------

Each hutch repository is hard-coded to use the central ``conda`` installs.
You can change this in your developer checkout by editing the ``xxxversion``
file. Take care not to commit changes to this file except to update the central
install version.

For ``python=3.6``, the central install is at ``/reg/g/pcds/pyps/conda/py36``.
It is managed using the `pcds-envs <https://github.com/pcdshub/pcds-envs>`_
module.

You can activate the base environment by calling
``source /reg/g/pcds/pyps/conda/py36env.sh pcds-0.6.0``, matching the
environment version number appropriately if this page is out of date.

Personal Install
----------------

You may wish to install ``hutch-python`` into your own environment for
development purposes. This can be achieved trivially if your environment is in
`conda <https://conda.io/docs>`_. If your environment is not in conda, I
highly suggest downloading `miniconda <https://conda.io/miniconda.html>`_
and giving it a try.

The requirements have not yet been consolidated into one conda channel, but we
plan to place everything in the ``pcds-tag`` channel in the future. Currently,
to pick up all dependencies, run this command:

``conda install hutch-python -c pcds-tag -c pydm-tag -c lightsource2-tag
-c defaults -c conda-forge``