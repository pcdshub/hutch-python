"""
Load Detector objects based on a camviewer config file
"""
import asyncio
import logging
from functools import partial
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool

from pcdsdevices.areadetector.detectors import PCDSAreaDetector

from .constants import SUCCESS_LEVEL

logger = logging.getLogger(__name__)
logger.success = partial(logger.log, SUCCESS_LEVEL)

main_event_loop = None


def read_camviewer_cfg(filename):
    """
    Read camviewer.cfg file and create detector objects.

    Parameters
    ----------
    filename: ``str``
        Full path to the camviewer.cfg file.

    Returns
    -------
    objs: ``{str: PCDSAreaDetector}``
        Each detector object, indexed by name.
    """
    info = interpret_cfg(filename)
    return load_cams(info)


def interpret_cfg(filename, pvnames=None):
    """
    Read camviewer.cfg file and interpret lines

    Parameters
    ----------
    filename: ``str``
        Full path to the camviewer.cfg file.

    Returns
    -------
    info: ``list of str``
        Valid inputs for build_cam
    """
    with open(filename) as f:
        lines = f.readlines()

    if pvnames is None:
        pvnames = set()
    return interpret_lines(lines, pvnames=pvnames)


def interpret_lines(lines, pvnames=None):
    """
    Create info list from string lines of a camviewer.cfg file.

    Parameters
    ----------
    lines: ``list of str``
        The python strings for each line of the config file

    pvnames: ``set``, optional
        For internal use only, to keep track of which PVs we're already
        planning to load so we don't make duplicate objects.

    Returns
    -------
    info: ``list of list str``
        Valid inputs for build_cam
    """
    info = []
    if pvnames is None:
        pvnames = set()

    for line in lines:
        line = line.strip()
        if not line or line[0] == '#':
            continue

        logger.debug(line)
        parts = line.split(',')
        parts = [p.strip() for p in parts]

        if parts[0].startswith('include'):
            try:
                inc = interpret_cfg(parts[0].split(' ')[1], pvnames=pvnames)
                info.extend(inc)
            except IndexError:
                err = 'Malformed include line "%s" in camviewer cfg, skipping.'
                logger.error(err, line)
                logger.debug(err, line, exc_info=True)
        elif len(parts) > 1:
            logger.debug(parts)
            pvname = get_det_prefix(parts[1])
            if pvname not in pvnames:
                logger.debug(pvname)
                pvnames.add(pvname)
                info.append(parts)

    return info


def load_cams(info):
    """
    Create detector object from string lines of a camviewer.cfg file.

    Parameters
    ----------
    info: ``list of list of str``
        Valid inputs for build_cam

    Returns
    -------
    objs: ``{str: PCDSAreaDetector}``
        Each detector object, indexed by name.
    """
    # Any cam that needs the event loop has to have one set in the thread
    global main_thread_loop
    try:
        main_thread_loop = asyncio.get_event_loop()
    except RuntimeError:
        # No loop, no worries
        main_thread_loop = None

    objs = {}
    logger.debug(info)
    pool = ThreadPool(cpu_count()-1)
    obj_list = pool.map(build_and_log, info)
    for obj in obj_list:
        if obj is not None:
            objs[obj.name] = obj
    return objs


def build_and_log(info_part):
    """
    Wrapper to run build_cam in a threadpool and handle errors

    Parameters
    ----------
    info_part: ``list of str``
        Valid input for build_cam

    Returns
    -------
    obj: ``PCDSAreaDetector``
        The loaded detector, or None.
    """
    # We sync with the main thread's loop so that they work as expected later
    if main_thread_loop is not None:
        asyncio.set_event_loop(main_thread_loop)
    try:
        obj = build_cam(*info_part)
        logger.success('Loaded %s', obj.name)
        return obj
    except UnsupportedConfig as exc:
        logger.debug('Skip non area detector cam %s',
                     exc.name, exc_info=True)
    except MalformedConfig:
        err = 'Skip malformed config %s'
        logger.error(err, info_part)
        logger.debug(err, info_part, exc_info=True)
    except TypeError:
        err = 'Malformed config %s in camviewer cfg, skipping.'
        logger.error(err, info_part)
        logger.debug(err, info_part, exc_info=True)
    except Exception:
        if len(info_part) >= 4:
            name = info_part[3]
        else:
            name = info_part
        err = ('Error loading %s in camviewer cfg. IOC '
               'probably down, skipping.')
        logger.error(err, name)
        logger.debug(err, info_part, exc_info=True)


def build_cam(cam_type, pv_info, evr, name, *args):
    """
    Create a single detector object, using camviewer.cfg information.

    Paramaters
    ----------
    cam_type: ``str``
        The first element in the camviewer config line, determines whether or
        not we have a detector class for the camera.

    pv_info: ``str``
        Second element in the line, determines which PVs to use.

    evr: ``str``
        Third element in the line, determines the EVR PVs. This is currently
        not used.

    name: ``str``
        Fourth element in th eline, determines the object's name.

    *args:
        Optional arguments that are unused.

    Returns
    -------
    cam: ``PCDSAreaDetector``
    """
    if not cam_type.startswith('GE'):
        raise UnsupportedConfig('Only cam type GE (area detector) supported.',
                                name=name)
    if not pv_info or not name:
        raise MalformedConfig(name=name)
    detector_prefix = get_det_prefix(pv_info)
    name = name.replace(' ', '_').lower()
    return PCDSAreaDetector(detector_prefix, name=name)


def get_det_prefix(pv_info):
    """
    Determines which prefix will be passed into the detector init.

    Parameters
    ----------
    pv_info: ``str``
        The second element in a camview cfg line.

    Returns
    -------
    detector_prefix: ``str``
        The prefix to use in the detector init.
    """
    pv_info = pv_info.split(';')
    try:
        detector_prefix = pv_info[1].strip()
    except IndexError:
        # Not provided in config, guess from image base
        detector_prefix = ':'.join(pv_info[0].split(':')[:-1])
    return detector_prefix + ':'


class UnsupportedConfig(Exception):
    def __init__(self, message=None, name=None):
        self.message = message or 'Unsupported config'
        self.name = name


class MalformedConfig(Exception):
    def __init__(self, message=None, name=None):
        self.message = message or 'Malformed config'
        self.name = name
