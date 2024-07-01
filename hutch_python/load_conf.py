"""
This module is responsible for reading and interpreting the ``conf.yml`` file.
The file's specification can be found on the `yaml_files` page.
"""
import logging
from copy import copy
from pathlib import Path
from socket import gethostname

from . import mpl_config  # noqa: F401

import matplotlib
import yaml
from archapp.interactive import EpicsArchive
from bluesky import RunEngine
from bluesky.callbacks.core import LiveTable
from bluesky.callbacks.mpl_plotting import initialize_qt_teleporter
from nabs.callbacks import BECOptionsPerRun
from pcdsdaq.daq import Daq
from pcdsdaq.scan_vars import ScanVars
from pcdsdaq.sim import set_sim_mode as set_daq_sim
from pcdsdevices.interface import setup_preset_paths

import hutch_python.ipython_session_timer

from . import calc_defaults, plan_defaults, sim, log_setup
from .cache import LoadCache
from .cam_load import read_camviewer_cfg
from .constants import CAMVIEWER_CFG, VALID_KEYS
from .debug import load_debug
from .exp_load import get_exp_objs
from .happi import DeviceLoadLevel, get_happi_objs, get_lightpath
from .lcls import global_devices, global_device_docs
from .namespace import class_namespace
from .ophyd_settings import setup_ophyd
from .obj_config import configure_objects
from .options import load_options
from .qs_load import get_qs_objs
from .plan_wrappers import initialize_wrapper_namespaces, register_plan
from .user_load import get_user_objs
from .utils import (get_current_experiment, hutch_banner, safe_load,
                    HelpfulNamespace, AbortSigintHandler,
                    SigquitHandler, abort_msg)

try:
    from elog import HutchELog
except ImportError:
    HutchELog = None

logger = logging.getLogger(__name__)


def load(cfg=None, args=None):
    """
    Read the config file and convert the yaml format into a ``dict``.

    This method:

    - Finds the hutch's launch directory
    - Modify the conf if specified by args
      - ``exp`` is an override for the experiment key
    - Loads the hutch's objects by calling `load_conf.load_conf`

    Parameters
    ----------
    cfg: ``str``, optional
        Path to the ``conf.yml`` file.
        If this is missing, we'll end up with a very empty environment.

    args: ``Namespace``, optional
        All of the arguments from the cli.

    Returns
    -------
    objs: ``dict{str: object}``
        All objects defined by ``conf.yml``. The strings are the names
        that will be accessible in the global namespace.
    """
    if cfg is None:
        conf = {}
        hutch_dir = None
    else:
        with open(cfg) as f:
            conf = yaml.safe_load(f)
        conf_path = Path(cfg)
        hutch_dir = conf_path.parent

    if args is not None and args.exp is not None:
        logger.debug('forcing experiment=%s', args.exp)
        conf['experiment'] = args.exp

    return load_conf(conf, hutch_dir=hutch_dir, args=args)


def load_conf(conf, hutch_dir=None, args=None):
    """
    Step through the object loading procedure, given a configuration.

    The procedure is:

    - Check the configuration for errors
    - Display the banner by calling `hutch_banner`
    - Use ``hutch`` key to create ``hutch.db`` importable namespace to
      stash the objects. This will be literally ``hutch.db`` if hutch is
      not provided, or the hutch name e.g. ``mfx.db``.
    - Evaluate the settings to determine which kind of daq object to create
      later.
    - Load debug tools
    - Load options
    - Set ophyd signal default timeouts
    - Create a ``logs`` namespace that allows the user to configure the
      logging settings.
    - Create a ``RunEngine``, ``RE``
    - Create a ``daq`` object with ``RE`` registered.
    - Import ``plan_defaults`` and include ``bp``, ``bps``, and ``bpp``.
    - Add a ``re`` namespace of ready-to-run scan functions as a mirror of
      ``bp``. Graft all daq-integrated scans onto the ``daq`` object.
    - Create a ``scan_pvs`` object, and ``enable`` it.
    - Use ``hutch`` and ``daq_platform`` keys to create the ``elog`` object
      and configure it to match the correct experiment.
    - Load the shared global devices for LCLS
    - Use ``db`` key to load devices from the ``happi`` beamline database
      and create a ``hutch_beampath`` object from ``lightpath``
    - Create an ``archive`` object for interfacing with the
      Archiver Appliance
    - Use ``hutch`` key to load detector objects from the ``camviewer``
      configuration file.
    - Load some simulated hardware and place it in the ``sim`` namespace.
    - Use ``experiment`` key to select the current experiment

        - If ``experiment`` was missing, autoselect experiment using
          ``hutch`` key

    - Use current experiment to load experiment objects from questionnaire
    - Use ``load`` key to bring up the user's ``beamline`` modules
    - Use current experiment to load experiment file
    - Create some default groups
    - Configure and load the position presets
    - Write the db.txt file to note what was loaded

    If a conf key is missing, we'll note it in a ``logger.info`` message.
    If an extra conf entry is found, we'll note it in a ``logger.warning``
    message.
    If an automatically selected file is missing, we'll note it in a
    ``logger.info`` message.
    All other errors will be noted in a logger.error message.

    Parameters
    ----------
    conf : dict
        ``dict`` interpretation of the original yaml file

    hutch_dir : ``Path`` or ``str``, optional
        ``Path`` object that points to the hutch's launch directory. This is
        the directory that includes the ``experiments`` directory and a
        hutchname directory e.g. ``mfx``
        If this is missing, we'll be unable to write the ``db.txt`` file,
        do relative filepath database selection for ``happi``,
        or establish a preset positions directory.

    args : argparse.Namespace, optional
        The namespace returned from the cli argument parsing, or None

    Returns
    ------
    objs: ``dict{str: object}``
        See the return value of `load`
    """
    # Warn user about excess config entries
    for key in conf:
        if key not in VALID_KEYS:
            txt = ('Found %s in configuration, but this is not a valid key. '
                   'The valid keys are %s')
            logger.warning(txt, key, VALID_KEYS)

    # Grab configurations from dict, set defaults, show missing
    try:
        hutch = conf['hutch']
        if isinstance(hutch, str):
            hutch = hutch.lower()
        else:
            logger.error('Invalid hutch conf %s, must be string.', hutch)
            hutch = None
    except KeyError:
        hutch = None
        logger.info("Missing hutch from conf. Will skip elog and cameras.")

    # Display the banner
    if hutch is None:
        hutch_banner()
    else:
        hutch_banner(hutch)

    try:
        db = conf['db']
        if isinstance(db, str):
            if db[0] == '/':
                db = Path(db)
            else:
                db = Path(hutch_dir) / db
        else:
            logger.error('Invalid db conf %s, must be string.', db)
            db = None
    except KeyError:
        db = None
        logger.info(
            'Missing db from conf. Will skip loading from shared database.')

    try:
        load_level_setting = conf['load_level']
        load_level = getattr(DeviceLoadLevel, load_level_setting.upper(),
                             DeviceLoadLevel.STANDARD)
    except KeyError:
        load_level = DeviceLoadLevel.STANDARD

    try:
        load = conf['load']
        if not isinstance(load, (str, list)):
            logger.error('Invalid load conf %s, must be string or list', load)
            load = None
    except KeyError:
        load = None
        logger.info('Missing load from conf. Will skip loading hutch files.')

    try:
        experiment = conf['experiment']
        if not isinstance(experiment, str):
            logger.error('Invalid experiment selection %s, must be a string '
                         'matching the elog experiment name.', experiment)
            experiment = None
    except KeyError:
        experiment = None
        if hutch is None:
            logger.info(
                "Missing hutch and experiment from conf. Will not "
                "load objects from questionnaire or experiment "
                "file."
            )

    try:
        obj_config = conf['obj_config']
        if isinstance(obj_config, str):
            if obj_config[0] == '/':
                obj_config = Path(obj_config)
            else:
                obj_config = Path(hutch_dir) / obj_config
        else:
            logger.error('Invalid obj_config conf %s, must be string.',
                         obj_config)
            obj_config = None
    except KeyError:
        obj_config = None
        logger.info(
            'Missing obj_config from conf. Will skip applying user settings to devices.'
        )
    try:
        # Configure whether we use the LCLS-I or LCLS-II daq
        daq_type = conf['daq_type']
    except KeyError:
        daq_type = 'lcls1'
        logger.info('Selected default daq type lcls1')
    else:
        if daq_type in ('lcls1', 'lcls1-sim', 'lcls2', 'nodaq'):
            logger.info(f'Selected valid daq type {daq_type}')
        else:
            logger.error('Selected invalid daq type! Will skip daq!')

    try:
        # Configure the daq host.
        # Required if lcls2 daq, unused if lcls1 daq.
        daq_host = conf['daq_host']
    except KeyError:
        if daq_type == 'lcls2':
            logger.error(
                'Missing required key "daq_host" in config! '
                'DAQ setup will fail!'
            )

    try:
        # This is an internal variable here for note-keeping. The ELog uses
        # this to determine if we are in the secondary or primary DAQ mode
        # In LCLS-II mode, this also sets the literal DAQ platform
        # (LCLS-I can pick it automatically)
        default_platform = True
        platform_info = conf['daq_platform']
        hostname = gethostname()
        try:
            daq_platform = platform_info[hostname]
            logger.info('Selected %s daq platform: %s',
                        hostname, daq_platform)
            default_platform = False
        except KeyError:
            daq_platform = platform_info['default']
            logger.info('Selected default %s daq platform: %s',
                        hutch, daq_platform)
    except KeyError:
        daq_platform = 0
        logger.info('Selected default hutch-python daq platform: 0')

    # Set the session timeout duration
    try:
        hutch_python.ipython_session_timer.configure_timeout(
            conf['session_timer'])
    except KeyError:
        hutch_python.ipython_session_timer.configure_timeout(172800)
        logger.info(
            'Missing session_timer value from conf. Set default value to 172800 seconds (48 hours).')

    # Make cache namespace
    cache = LoadCache((hutch or 'hutch') + '.db', hutch_dir=hutch_dir)

    # Load debug tools
    with safe_load('debug tools'):
        load_debug(cache)

    # Load options
    with safe_load('options'):
        load_options(cache)

    # Configure ophyd
    with safe_load('configure ophyd'):
        setup_ophyd()

    cache(
        logs=HelpfulNamespace(
            log_objects=log_setup.log_objects,
            log_objects_off=log_setup.log_objects_off,
            get_log_directory=log_setup.get_log_directory,
            get_session_logfiles=log_setup.get_session_logfiles,
            get_console_level_name=log_setup.get_console_level_name,
            set_console_level=log_setup.set_console_level,
            debug_mode=log_setup.debug_mode,
            debug_context=log_setup.debug_context,
            filter=log_setup.get_object_filter("console"),
            file_filter=log_setup.get_object_filter("debug"),
        )
    )

    # Make RunEngine
    with safe_load('run engine'):
        RE = RunEngine({}, context_managers=[AbortSigintHandler,
                                             SigquitHandler])
        RE.pause_msg = abort_msg
        initialize_qt_teleporter()
        bec = BECOptionsPerRun()
        if matplotlib.get_backend() not in {"Qt5Agg", "QtAgg"}:
            logger.warning(
                'Disabling bluesky scan plots. Matplotlib config must '
                'be set up for qt5 for bluesky scans to work!'
            )
            bec.disable_plots()

        RE.subscribe(bec)
        # Enable scientific notation for big/small numbers in LiveTable
        LiveTable._FMT_MAP['number'] = 'g'
        cache(RE=RE, bec=bec)
        cache.doc(
            RE='Bluesky plan executor.',
            bec='Bluesky best-effort callback for visualization settings.',
        )

    # Inline calculations
    with safe_load('calc utils'):
        cache(calc=calc_defaults.calc_namespace)
        cache.doc(calc='Namespace of calculation utilities.')

    # Daq
    with safe_load('daq'):
        if daq_type.startswith('lcls1'):
            if daq_type == 'lcls1-sim' or (args and args.sim):
                set_daq_sim(True)
            cache(daq=Daq(RE=RE, hutch_name=hutch))
            cache.doc(daq='LCLS1 DAQ interface object.')
        elif daq_type == 'lcls2':
            # Warning for users of the --sim flag
            if args is not None and args.sim:
                logger.warning('Sim mode not implemented for lcls2 DAQ!')
                logger.warning('Instantiating live DAQ!')
            # Optional dependency
            from psdaq.control.DaqControl import DaqControl  # NOQA
            from psdaq.control.BlueskyScan import BlueskyScan  # NOQA
            daq_control = DaqControl(
                host=daq_host,
                platform=daq_platform,
                timeout=10000,
            )
            instr = daq_control.getInstrument()
            if instr is None:
                logger.error('Failed to connect to LCLS-II DAQ')
            start_state = daq_control.getState()
            if start_state == 'error':
                logger.error('DAQ is in an error state.')
            daq_bluesky = BlueskyScan(
                daq_control,
                daqState=start_state,
            )
            cache(daq=daq_bluesky)
            cache.doc(daq='LCLS2 DAQ interface object.')
        elif daq_type == 'nodaq':
            logger.info('Skip daq because daq_type is nodaq.')
        else:
            raise RuntimeError('Not loading daq, invalid daq_type.')

    # Collect Plans and Plan Wrappers
    with safe_load('bluesky plans'):
        run_namespace = initialize_wrapper_namespaces(
            RE=RE,
            plan_namespace=plan_defaults.plans,
            daq=getattr(cache.objs, 'daq', None),
        )
        cache(
            bp=plan_defaults.plans,
            bps=plan_defaults.plan_stubs,
            bpp=plan_defaults.preprocessors,
            re=run_namespace,
            register_plan=register_plan,
        )
        cache.doc(
            bp='Namespace of full bluesky plans.',
            bps='Namespace of bluesky plan building blocks (stubs).',
            bpp='Namespace of bluesky plan preprocessors.',
            re='Wrapped plans for quick running.',
        )

    # Scan PVs
    if hutch is not None:
        with safe_load('scan_pvs'):
            scan_pvs = ScanVars(f'{hutch.upper()}:SCAN',
                                name='scan_pvs', RE=RE)
            scan_pvs.enable()
            cache(scan_pvs=scan_pvs)
            cache.doc(scan_pvs='LCLS scan status PVs.')

    # Elog
    if hutch is not None:
        with safe_load('elog'):
            if HutchELog is None:
                txt = 'Skip elog, module not available.'
                logger.warning(txt)
                raise RuntimeError(txt)
            # Use the fact if we we used the default_platform or not to decide
            # whether we are in a specialty station or not
            if default_platform:
                logger.debug("Using primary experiment ELog")
                kwargs = dict()
            else:
                logger.info("Configuring ELog to post to secondary experiment")
                kwargs = {'station': '1'}
            cache(elog=HutchELog.from_conf(hutch.upper(), **kwargs))
            cache.doc(elog='Elog posting interface object.')

    # Shared global devices for LCLS
    with safe_load('lcls PVs'):
        cache(**global_devices())
        cache.doc(**global_device_docs)

    # Happi db and Lightpath
    if db is not None:
        with safe_load('database'):
            lc = get_lightpath(db, hutch)

            # Gather relevant objects given the BeamPath
            happi_objs = get_happi_objs(db, lc, hutch, load_level=load_level)
            cache(**happi_objs)

            # create and store beampath
            if lc is not None:
                bp = lc.active_path(hutch.upper())
                beampath_name = f"{hutch.lower()}_beampath"
                cache(**{beampath_name: bp})
                cache.doc(**{beampath_name: 'Lightpath beam path object.'})

                cache(**{'light_ctrl': lc})
                cache.doc(light_ctrl='Lightpath LightController object')

    # ArchApp
    with safe_load('archapp'):
        cache(archive=EpicsArchive())
        cache.doc(archive='Archiver interface for getting historical data.')

    # Camviewer
    if hutch is not None:
        with safe_load('camviewer config'):
            objs = read_camviewer_cfg(CAMVIEWER_CFG.format(hutch))
            cache(camviewer=HelpfulNamespace(**objs))
            cache.doc(camviewer='Namespace of configured camviewer cameras.')

    # Simulated hardware
    with safe_load('simulated hardware'):
        cache(sim=sim.get_hw())
        cache.doc(sim='Namespace of simulated hardware.')

    # Auto select experiment if we need to
    if experiment is None:
        if hutch is not None:
            try:
                # xpplp1216
                experiment = get_current_experiment(hutch)
                logger.info('Selected active experiment %s', experiment)
            except Exception:
                err = 'Failed to select experiment automatically'
                logger.error(err)
                logger.debug(err, exc_info=True)

    # Process experiment name a bit
    if experiment is not None:
        if hutch in experiment:
            full_expname = experiment
            raw_expname = experiment.replace(hutch, '', 1)
        else:
            full_expname = hutch + experiment
            raw_expname = experiment

    # Load questionnaire
    if experiment is not None:
        qs_objs = get_qs_objs(full_expname)
        cache(**qs_objs)

    # Load user/beamline files
    if load is not None:
        load_objs = get_user_objs(load)
        cache(**load_objs)

    # Load experiment file
    if experiment is not None:
        user = get_exp_objs(raw_expname)
        for name, obj in qs_objs.items():
            setattr(user, name, obj)
        cache(x=user, user=user)
        cache.doc(user='User experiment object')

    # Default namespaces
    with safe_load('default groups'):
        default_class_namespace('ophyd.PositionerBase', 'motors', cache)
        default_class_namespace('Slits', 'slits', cache)
        default_class_namespace('pcdsdaq.ami.AmiDet', 'detectors', cache)

        # Hotfix/disabled until we fix issues here
        # Tree namespace can cause havoc and break top-level devices
        #
        # if hutch is not None:
        #     tree = tree_namespace(scope='hutch_python.db')
        #     # Prune meta, remove branches with only one object
        #     for name, space in tree.__dict__.items():
        #         if count_ns_leaves(space) > 1:
        #             cache(**{name: space})

        all_objs = copy(cache.objs)
        cache(a=all_objs, all_objects=all_objs)
        cache.doc(
            motors='Namespace of all positioner objects.',
            slits='Namespace of all slits objects.',
            detectors='Namespace of all ami detector objects.',
            all_objects='Namespace of all loaded objects.',
        )

    # Install Presets
    if hutch_dir is not None:
        with safe_load('position presets'):
            presets_dir = Path(hutch_dir) / 'presets'
            beamline_presets = presets_dir / 'beamline'
            preset_paths = [presets_dir, beamline_presets]
            if experiment is not None:
                experiment_presets = presets_dir / raw_expname
                preset_paths.append(experiment_presets)
            for path in preset_paths:
                if not path.exists():
                    path.mkdir()
                    path.chmod(0o777)
            if experiment is None:
                setup_preset_paths(hutch=beamline_presets)
            else:
                setup_preset_paths(hutch=beamline_presets,
                                   exp=experiment_presets)

    # configure objects
    if obj_config is not None:
        configure_objects(obj_config, all_objs)

    # Write db.txt info file to the user's module
    try:
        cache.write_file()
    except OSError:
        logger.warning('No permissions to write db.txt file')

    return cache.objs.__dict__


def default_class_namespace(cls, name, cache):
    """
    Create a class namespace and add it to the cache.

    This is an internal utility function for `load_conf.load_conf` that creates
    an `IterableNamespace`, names it, gives it a shortened name, and then
    registers both names to the `LoadCache` if the namespace isn't empty.

    Parameters
    ----------
    cls: ``type`` or ``str``
        The class to use for the namespace

    name: ``str``
        The name of the namespace

    cache: `LoadCache`
    """
    objs = class_namespace(cls, scope='hutch_python.db')
    if len(objs) > 0:
        cache(**{name: objs, name[0]: objs})
