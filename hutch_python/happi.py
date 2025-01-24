import enum
import inspect
import logging
import fnmatch
from typing import Dict, List, Optional, Union
from .utils import is_a_range, is_number

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


def search_parser(
    client: happi.Client,
    use_glob: bool,
    search_criteria: list[str],
) -> list[happi.SearchResult]:
    """
    Parse the user's search criteria and return the search results.

    ``search_criteria`` must be a list of key=value strings.
    If key is omitted, it will be assumed to be "name".

    Parameters
    ----------
    client : Client
        The happi client that we'll be doing searches in.
    use_glob : bool
        True if we're using glob matching, False if we're using
        regex matching.
    search_criteria : list of str
        The user's search selection from the command line.
    """
    # Get search criteria into dictionary for use by client
    client_args = {}
    range_list = []
    regex_list = []
    range_found = False

    for user_arg in search_criteria:
        if '=' in user_arg:
            criteria, value = user_arg.split('=', 1)
        else:
            criteria = 'name'
            value = user_arg

        # raise exception here
        if criteria in client_args:
            raise Exception(
                f"Received duplicate search criteria {criteria}={value!r} "
                f"(was {client_args[criteria]!r})"
            )

        if is_a_range(value):
            start, stop = value.split(',')
            start = float(start)
            stop = float(stop)
            if start < stop:
                new_range_list = client.search_range(criteria, start, stop)
            else:
                # raise exception here
                raise Exception('Invalid range, make sure start < stop')

            if not range_found:
                # if first range, just replace
                range_found = True
                range_list = new_range_list
            else:
                # subsequent ranges, only take intersection
                range_list = set(new_range_list) & set(range_list)

            if not range_list:
                # we have searched via a range query.  At this point
                # no matches, or intesection is empty. abort early
                logger.error("No items found")
                return []

            continue

        elif is_number(value):
            if float(value) == int(float(value)):
                # value is an int, allow the float version (optional .0)
                logger.debug(f'looking for int value: {value}')
                value = f'^{int(float(value))}(\\.0+$)?$'

                # don't translate from glob
                client_args[criteria] = value
                continue
            else:
                value = str(float(value))
        else:
            logger.debug('Value %s interpreted as string', value)

        if use_glob:
            client_args[criteria] = fnmatch.translate(value)
        else:  # already using regex
            client_args[criteria] = value

    regex_list = client.search_regex(**client_args)

    # Gather final results
    final_results = []
    if regex_list and not range_list:
        # only matched with one search_regex()
        final_results = regex_list
    elif range_list and not regex_list:
        # only matched with search_range()
        final_results = range_list
    elif range_list and regex_list:
        # find the intersection between regex_list and range_list
        final_results = set(range_list) & set(regex_list)
    else:
        logger.debug('No regex or range items found')

    if not final_results:
        logger.error('No items found')

    return final_results


def get_happi_objs(
    db: str,
    light_ctrl: LightController,
    endstation: str,
    load_level: DeviceLoadLevel = DeviceLoadLevel.STANDARD,
    exclude_devices: Optional[List[str]] = None,
    additional_devices: Optional[Dict[str, Union[str, bool]]] = None
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

    exclude_devices: ``list[str]``
        list of devices that should be excluded when loading

    additional_devices: ``Dict[str, Union[str, bool]]``
        a dictionary containing happi search terms as well as a 'match_all' 
        key that indicates a union or intersection search

    Returns
    -------
    objs: ``dict``
        A mapping from item name to item
    """

    # Explicitly set exclude_devices and additional_devices to empty
    # containers to avoid mutable default arguments issue.
    if not exclude_devices:
        exclude_devices = []

    if not additional_devices:
        additional_devices = {}

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

    # # Parse additional_devices
    # # check match_all and delete
    # match_all = additional_devices['match_all']     # False
    # del additional_devices['match_all']

    # # additional_devices is now {'beamline': ['IP1_MODS'], 'name': ['lm1k4_inj_*'], 'z': ['-1', '1']}
    # if match_all:
    #     # run everything in search_parser() then do do containers.extend()
    #     pass
    # else:
    #     # run each element of the list in search_parser and do containers.extend() for each set of results
    #     final_results = search_parser(
    #         client=client,
    #         use_glob=True,
    #         search_criteria=search_criteria,
    #     )
    #     pass

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
