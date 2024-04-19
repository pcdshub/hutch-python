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
``source /reg/g/pcds/pyps/conda/py36env.sh``.
This will give you the latest, you can pick an older environment with
``source /reg/g/pcds/pyps/conda/py36env.sh $ENVNAME``. If you take latest and
run ``conda env list``, you'll see all of the options.

Personal Install
----------------

You may wish to install ``hutch-python`` into your own environment for
development purposes. This can be achieved trivially if your environment is in
`conda <https://conda.io/docs>`_. If your environment is not in conda, I
highly suggest downloading `miniconda <https://conda.io/miniconda.html>`_
and giving it a try.

To pick up all dependencies, run this command:

``conda install hutch-python -c pcds-tag -c defaults -c conda-forge``
