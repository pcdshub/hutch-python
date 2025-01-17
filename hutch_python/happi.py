import enum
import inspect
import logging
from typing import List, Dict

import happi
import ophyd
from happi.loader import load_devices

try:
    import lightpath
    from lightpath import LightController
    from lightpath.config import beamlines
except ImportError:
    lightpath = None
    LightController = None
    beamlines = None

logger = logging.getLogger(__name__)


class DeviceLoadLevel(enum.IntEnum):
    # HUTCH = 0  # TODO: Figure out how to gather only hutch devices
    UPSTREAM = 1
    STANDARD = 2
    ALL = 3


def get_happi_objs(
    db: str,
    light_ctrl: LightController,
    endstation: str,
    load_level: DeviceLoadLevel = DeviceLoadLevel.STANDARD,
    exclude_devices: List[str] = None,
    additional_devices: Dict[str, List[str]] = None
) -> dict[str, ophyd.Device]:
    """
    Get the relevant items for ``endstation`` from the happi database ``db``.

    This depends on a JSON ``happi`` database stored somewhere in the file
    system and handles setting up the ``happi.Client`` and querying the data
    base for items.

    Uses the paths found by the LightController, but does not use it to
    load the devices so we can do so ourselves and log load times.

    Parameters
    ----------
    db: ``str``
        path to the happi database

    light_ctrl: lightpath.LightController
        LightController instance constructed from the happi db

    endstation: ``str``
        Name of hutch

    load_level: ``DeviceLoadLevel``
        load all or standard devices

    exclude_devices: ``List[str]``
        list of devices that should be excluded when loading

    additional_devices: ``Dict[str, List[str]]``
        devices are loaded based on this dictionary of happi search terms

    Returns
    -------
    objs: ``dict``
        A mapping from item name to item
    """

    # Explicitly set exclude_devices and additional_devices to empty lists to
    # avoid mutable default arguments issue.
    if not exclude_devices:
        exclude_devices = []

    if not additional_devices:
        additional_devices = []

    # Load the happi Client
    if None not in (light_ctrl, lightpath):
        client = light_ctrl.client
    else:
        client = happi.Client(path=db)
    containers = list()

    if load_level == DeviceLoadLevel.ALL:
        results = client.search(active=True)
        containers.extend(res.item for res in results)

    elif light_ctrl is None or (endstation.upper() not in light_ctrl.beamlines):
        # lightpath was unavailable, search by beamline name
        reqs = dict(beamline=endstation.upper(), active=True)
        results = client.search(**reqs)
        containers.extend(res.item for res in results)

    else:
        # if lightpath exists, we can grab upstream devices
        dev_names = set()
        paths = light_ctrl.beamlines[endstation.upper()]
        for path in paths:
            dev_names.update(path)

        # gather happi items for each of these
        for name in dev_names:
            results = client.search(name=name)
            containers.extend(res.item for res in results)

        if load_level >= DeviceLoadLevel.STANDARD:
            # also any device with the same beamline name
            # since lightpath only grabs lightpath-active devices
            beamlines = {it.beamline for it in containers}
            beamlines.add(endstation.upper())

            for line in beamlines:
                # Assume we want hutch items that are active
                # items can be lightpath-inactive
                reqs = dict(beamline=line, active=True)
                results = client.search(**reqs)
                blc = [res.item for res in results
                       if res.item.name not in dev_names]
                # Add the beamline containers to the complete list
                if blc:
                    containers.extend(blc)

    if len(containers) < 1:
        logger.warning(f'{len(containers)} active devices found for '
                       'this beampath')

    # Do not load excluded devices
    for device in containers.copy():
        if device.name in exclude_devices:
            containers.remove(device)

    # Load additional devices
    for key in additional_devices:
        for value in key:
            results = client.search_regex(key=value)
            containers.extend(results)
            results = []

    # Remove duplicate devices before loading
    containers = list(set(containers))

    return _load_devices(*containers)


def _load_devices(*containers: happi.HappiItem):
    """
    Load objects specified by the provided containers.
    Optionally keeps track of loading times and logs them

    Returns
    -------
    types.SimpleNamespace or Mapping
        namespace mapping device name to its ophyd.Device
    """

    # Instantiate the devices needed
    sig = inspect.signature(load_devices)
    if "include_load_time" in sig.parameters:
        kwargs = dict(include_load_time=True, load_time_threshold=0.5)
    else:
        kwargs = {}
    dev_namespace = load_devices(*containers, pprint=False, **kwargs)
    return dev_namespace.__dict__


def get_lightpath(db: str, hutch: str) -> LightController:
    """
    Create a ``lightpath.LightController`` from relevant ``happi`` objects.

    Parameters
    ----------
    db: ``str``
        Path to database

    hutch: ``str``
        Name of hutch

    Returns
    -------
    path: ``lightpath.LightController``
        Object that contains the a representation of the facility graph.  Can
        be used to access a ``BeamPath``, which provides a convenient way to
        visualize all the devices that may block the beam on the way to the
        interaction point.
    """
    if None in (lightpath, beamlines):
        logger.warning('Lightpath module is not available.')
        return None

    # Load the happi Client
    client = happi.Client(path=db)

    # Allow the lightpath module to create a path
    lc = lightpath.LightController(client, endstations=[hutch.upper()])

    # Return paths (names only) seen by the LightController
    # avoid loding the devices so hutch-python can keep track of it

    return lc
