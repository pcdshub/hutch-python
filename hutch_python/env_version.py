"""
Utilities for getting relevant environment information.
"""
from __future__ import annotations

import importlib.metadata
import logging
import os
import os.path
import pkgutil

logger = logging.getLogger(__name__)

_dev_ignore_list = ['ami', 'pdsapp']


def not_ignored(path: list[str], ignores: list[str] = None) -> bool:
    """ Return True if _dev_ignore_list isn't in path or empty """
    if ignores is None:
        ignores = _dev_ignore_list
    return bool(path and not any(s in path for s in ignores))


def log_env() -> None:
    """Collect environment information and log at appropriate levels."""
    dev_pkgs = get_standard_dev_pkgs()
    if dev_pkgs:
        logger.debug(
            'Using conda env %s with dev packages %s',
            get_conda_env_name(),
            ', '.join(sorted(dev_pkgs)),
        )
    else:
        logger.debug(
            'Using conda env %s with no dev packages',
            get_conda_env_name(),
        )
    logger.debug(dump_env())


def dump_env() -> list[str]:
    """
    Get all packages and versions from the current environment.
    conda list is slow, use importlib.metadata.distributions instead
    this might miss dev overrides
    """
    return sorted(str(dist.name) for dist in importlib.metadata.distributions())


def get_conda_env_name() -> str:
    """Get the name of the conda env, or empty string if none."""
    env_dir = os.environ.get('CONDA_PREFIX', '')
    return os.path.basename(env_dir)


def get_standard_dev_pkgs() -> set[str]:
    """Check the standard dev package locations for hutch-python"""
    pythonpath = os.environ.get('PYTHONPATH', '')
    if not pythonpath:
        return set()
    paths = pythonpath.split(os.pathsep)
    valid_paths = filter(not_ignored, paths)
    pkg_names = {
        n.name for n in pkgutil.iter_modules(path=valid_paths)
        if n.ispkg
    }

    return pkg_names


def get_env_info() -> str:
    """ Collect environment information and format as banner """
    conda_ver = get_conda_env_name()
    dev_pkgs = sorted(get_standard_dev_pkgs())

    banner = (
        'Environment Information\n'
        f'  Conda Environment: {conda_ver}\n'
        f'  Development Packages: {" ".join(dev_pkgs)}'
    )

    return banner
