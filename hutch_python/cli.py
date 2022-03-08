"""
This module defines the command-line interface arguments for the
``hutch-python`` script. It also provides utilities that are only used at
startup.
"""
import argparse
import logging
import os
import sys
from pathlib import Path

import IPython
import matplotlib
from cookiecutter.main import cookiecutter
from IPython import start_ipython
from pcdsutils.profile import profiler_context
from traitlets.config import Config

from .constants import CONDA_BASE, DIR_MODULE
from .load_conf import load
from .log_setup import configure_log_directory, debug_mode, setup_logging

DEFAULT_PROFILE_MODULES = [
    'archapp',
    'elog',
    'happi',
    'lightpath',
    'nabs',
    'pcdscalc',
    'pcdsdaq',
    'pcdsdevices',
    'pcdsutils',
]

logger = logging.getLogger(__name__)
opts_cache = {}

# Define the parser
parser = argparse.ArgumentParser(prog='hutch-python',
                                 description='Launch LCLS Hutch Python')
parser.add_argument('--cfg', required=False, default=None,
                    help='Configuration yaml file')
parser.add_argument('--exp', required=False, default=None,
                    help='Experiment number override')
parser.add_argument('--debug', action='store_true', default=False,
                    help='Start in debug mode')
parser.add_argument('--sim', action='store_true', default=False,
                    help='Run with simulated DAQ (lcls1 only)')
parser.add_argument('--create', action='store', default=False,
                    help='Create a new hutch deployment')
parser.add_argument('--startup-only', action='store_true', default=False,
                    help="Don't enter ipython, only check the startup.")
parser.add_argument(
    '--profile',
    nargs='*',
    help=(
        'Run the profiler, tracking the functions in the given modules. '
        'If no arguments are given, run with the default modules of '
        f'{", ".join(DEFAULT_PROFILE_MODULES)}.'
    )
)
parser.add_argument(
    '--profile-output',
    action='store',
    help=(
        'File path to store the profile output in. Implies --profile, '
        'and triggers --profile if needed.'
    ),
)
parser.add_argument('script', nargs='?',
                    help='Run a script instead of running interactively')

# Append to module docs
__doc__ += '\n::\n\n    ' + parser.format_help().replace('\n', '\n    ')


def configure_tab_completion(ipy_config):
    """
    Disable Jedi and tweak IPython tab completion.

    Parameters
    ----------
    ipy_config : traitlets.config.Config
        IPython configuration.
    """
    # Old API for disabling Jedi. Keep in just in case API changes back.
    ipy_config.InteractiveShellApp.Completer.use_jedi = False
    # New API for disabling Jedi (two access points documented, use both)
    ipy_config.Completer.use_jedi = False
    ipy_config.IPCompleter.use_jedi = False
    try:
        # Monkeypatch IPython completion - we need it to respect __dir__
        # when Jedi is disabled.
        # Details: https://github.com/pcdshub/pcdsdevices/issues/709
        # First, access it to see that the internals have not changed:
        IPython.core.completer.dir2
    except AttributeError:
        logger.debug('Looks like the IPython API changed!')
    else:
        # Then monkeypatch it in:
        IPython.core.completer.dir2 = dir


def configure_ipython_session():
    """
    Configure a new IPython session.

    Returns
    -------
    ipy_config : traitlets.config.Config
        IPython configuration.
    """
    ipy_config = Config()
    # Important Utilities
    ipy_config.InteractiveShellApp.extensions = [
        'hutch_python.ipython_log',
        'hutch_python.bug'
    ]
    # Matplotlib setup for ipython (automatically do %matplotlib)
    backend = matplotlib.get_backend().replace('Agg', '').lower()
    ipy_config.InteractiveShellApp.matplotlib = backend
    if backend == 'agg':
        logger.warning('No matplotlib rendering available. '
                       'Methods that create plots will not '
                       'function properly.')

    # Disable reformatting input with black
    ipy_config.TerminalInteractiveShell.autoformatter = None
    # Set up tab completion modifications
    configure_tab_completion(ipy_config)
    return ipy_config


def main():
    # Parse the user's arguments
    args = parser.parse_args()
    do_profile = False
    module_names = DEFAULT_PROFILE_MODULES
    filename = None
    if args.profile is None:
        # No profile arg
        do_profile = False
    elif args.profile:
        # Profile with given modules
        do_profile = True
        module_names = args.profile
    else:
        # Profile with default modules
        do_profile = True
    if args.profile_output:
        # Profile to a specific folder
        do_profile = True
        filename = args.profile_output
    if do_profile:
        with profiler_context(
            module_names=module_names,
            filename=filename,
        ):
            launch(args)
    else:
        launch(args)


def launch(args):
    """
    Do the full hutch-python launch sequence.

    Parses the user's cli arguments and distributes them as needed to the
    setup functions.
    """
    # Set up logging first
    if args.cfg is None:
        log_dir = None
    else:
        log_dir = os.path.join(os.path.dirname(args.cfg), 'logs')

    configure_log_directory(log_dir)
    setup_logging()

    # Debug mode next
    if args.debug:
        debug_mode(True)

    # Do the first log message, now that logging is ready
    logger.debug('cli starting with args %s', args)

    # Options that mean skipping the python environment
    if args.create:
        hutch = args.create
        envs_dir = CONDA_BASE / 'envs'
        if envs_dir.exists():
            # Pick most recent pcds release in our common env
            base = str(CONDA_BASE)
            path_obj = sorted(envs_dir.glob('pcds-*'))[-1]
            env = path_obj.name
        else:
            # Fallback: pick current env
            try:
                base = str(Path(os.environ['CONDA_EXE']).parent.parent)
                env = os.environ['CONDA_DEFAULT_ENV']
            except KeyError:
                # Take a stab at some non-conda defaults; ideally these would
                # be configurable with argparse.
                base = Path(sys.executable).parent
                env = hutch
        logger.info(('Creating hutch-python dir for hutch %s using'
                     ' base=%s env=%s'), hutch, base, env)
        cookiecutter(str(DIR_MODULE / 'cookiecutter'), no_input=True,
                     extra_context=dict(base=base, env=env, hutch=hutch))
        return

    # Save whether we are an interactive session or a script session
    opts_cache['script'] = args.script

    # Load objects based on the configuration file
    objs = load(cfg=args.cfg, args=args)

    script = opts_cache.get('script')
    if args.startup_only:
        return
    if script is None:
        # Finally start the interactive session
        start_ipython(argv=['--quick'], user_ns=objs,
                      config=configure_ipython_session())
    else:
        # Instead of setting up ipython, run the script with objs
        with open(script) as fn:
            code = compile(fn.read(), script, 'exec')
            exec(code, objs, objs)
