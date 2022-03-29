"""
Utilities for getting relevant environment information.
"""
from __future__ import annotations

import logging
import os
import os.path
import platform
import pkg_resources


logger = logging.getLogger(__name__)


def log_env() -> None:
    """Collect environment information and log at appropriate levels."""
    dev_pkgs = get_standard_dev_pkgs()
    if dev_pkgs:
        logger.info(
            'Using conda env %s with dev packages %s',
            get_conda_env_name(),
            ', '.join(sorted(dev_pkgs)),
        )
    else:
        logger.info(
            'Using conda env %s with no dev packages',
            get_conda_env_name(),
        )
    logger.debug(dump_env())


def dump_env() -> list[str]:
    """
    Get the full env spec.

    conda list is slow, use pkg_resources instead
    this might miss dev overrides
    """
    return sorted(str(pkg) for pkg in pkg_resources.working_set)


def get_conda_env_name() -> str:
    """Get the name of the conda env, or empty string if none."""
    env_dir = os.environ.get('CONDA_PREFIX', '')
    return os.path.basename(env_dir)


def get_standard_dev_pkgs() -> set[str]:
    """Check the standard dev package locations for hutch-python"""
    pythonpath = os.environ.get('PYTHONPATH', '')
    if not pythonpath:
        return set()
    pkg_names = set()
    for part in pythonpath.split(':'):
        if 'devpath' in part:
            pkg_names.update(os.listdir(part))
    return pkg_names
