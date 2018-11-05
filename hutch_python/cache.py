"""
This module is responsible for accumulating all loaded objects and making sure
they are available in the ``xxx.db`` virtual module. It is used extensively in
`load_conf.load_conf`.
"""
from importlib import import_module
from pathlib import Path
import datetime
import logging
import sys

from .utils import IterableNamespace

logger = logging.getLogger(__name__)


class LoadCache:
    """
    Class that accumulates objects in a virtual module.

    This virtual module can be imported from as if it were a normal module.

    Parameters
    ----------
    module: ``str``
        Name of the virtual module to create. If the module has the same
        name as a real module, the real module will be masked.

    hutch_dir: ``Path``, optional
        This allows us to write a ``db.txt`` file to let the user know what
        objects get imported.

    **objs: kwargs
        Initial objects to place into the namespace

    Attributes
    ----------
    objs: `IterableNamespace`
        This is a namespace containing all the objects that have been attached
        to the ``LoadCache``.

    all_objs: ``dict``
        The dictionary corresponding to ``objs``.

    group_objs: ``dict``
        A subset of ``all_objs`` to be considered for tree grouping

    groups: ``list`` of ``str``
        Valid group names
    """
    groups = ['daq', 'det', 'las',
              'fee', 'amo', 'sxr', 'hx2', 'xpp',
              'xrt', 'pbt', 'xcs', 'mfx', 'cxi', 'mec']

    def __init__(self, module, hutch_dir=None, **objs):
        self.objs = IterableNamespace(**objs)
        self.all_objs = self.objs.__dict__
        self.group_objs = {}
        self.hutch_dir = hutch_dir
        self.module = module
        self.spoof_module(module)
        self.spoof_module('hutch_python.db')

    def spoof_module(self, module_name):
        """
        Create a fake module that is actually self.objs
        """
        # Check for real module that it needs to be slipped into
        module_parts = module_name.split('.')
        parent = '.'.join(module_parts[:-1])
        if parent:
            try:
                parent_module = import_module(parent)
                setattr(parent_module, module_parts[-1], self.objs)
            except ImportError:
                logger.debug('Skip patching parent module %s, does not import',
                             parent, exc_info=True)

        # Place it here so it looks like we've already imported it
        sys.modules[module_name] = self.objs

    def __call__(self, **objs):
        """
        Add objects to the namespace.

        Parameters
        ----------
        **objs: kwargs
            The key will is the namespace-accessible name, and the object
            is the object we are adding.
        """
        self.all_objs.update(**objs)
        for name, obj in objs.items():
            if name.split('_')[0] in self.groups:
                self.group_objs[name] = obj

    def write_file(self):
        """
        Write a ``db.txt`` file in the hutch's directory. This file informs
        the user which objects get loaded by ``hutch-python``.
        """
        if self.hutch_dir is not None:
            parts = self.module.split('.')
            parts[-1] = parts[-1] + '.txt'
            db_path = self.hutch_dir / Path('/'.join(parts))
            text = (header.format(parts[0])
                    + body.format(datetime.datetime.now()))
            for name, obj in self.all_objs.items():
                text += '{:<20} {}\n'.format(name, obj.__class__)
            if not db_path.exists():
                db_path.touch()
                db_path.chmod(0o666)
            with db_path.open('w') as f:
                f.write(text)


# For writing the files
header = """
The objects referenced in this file are populated by the {0}python\n
initialization. If you wish to use devices from this file, import\n
them from {0}.db after calling the {0}python startup script.\n\n
"""
body = ('hutch-python last loaded on {}\n'
        'with the following objects:\n\n')
