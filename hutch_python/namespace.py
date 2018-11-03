"""
This module provides utilities for grouping objects into namespaces.
"""
from collections import defaultdict
from inspect import isfunction
from keyword import iskeyword
import logging

from ophyd import Device

from .utils import IterableNamespace, find_class, extract_objs

logger = logging.getLogger(__name__)


def class_namespace(cls, scope=None):
    """
    Create a ``namespace`` that contains objects of a specific type.

    Parameters
    ----------
    cls: ``type`` or ``str``

    scope: ``module``, ``namespace``, or ``list`` of these
        Every object attached to the given modules will be considered for the
        `class_namespace`. If ``scope`` is omitted, we'll check all objects
        loaded by ``hutch-python`` and everything in the caller's global frame.
        If anything is an instance of ``ophyd.Device``, we'll also include the
        object's components as part of the scope, using the ``name`` attribute
        to identify them rather than the attribute name on the device. This
        will continue recursively, skipping lazy and dynamic components.

    Returns
    -------
    namespace: `IterableNamespace`
    """
    logger.debug('Create class_namespace cls=%s, scope=%s', cls, scope)
    class_space = IterableNamespace()
    scope_objs = extract_objs(scope=scope, stack_offset=1)

    # Resolve str arguments for cls
    if isinstance(cls, str):
        if cls != 'function':
            try:
                cls = find_class(cls)
            except Exception as exc:
                err = 'Type {} could not be loaded'
                logger.error(err.format(cls))
                logger.debug(exc, exc_info=True)
                return class_space

    # Mapping from Device class to list of lists of attrs that lead us to
    # subdevices of the correct type
    cache = {}

    def inspect_device_cls(device_cls, desired_cls, cache):
        """
        Recursive helper function.

        Gets a list of components of device_class that match desired_cls,
        skipping lazy components. Uses cache to improve speed for hutch-python
        environments with large numbers of objects with the same class.
        """
        try:
            return cache[device_cls]
        except KeyError:
            attrs = []
            if issubclass(device_cls, Device):
                logger.debug('Checking subdevices for class %s', device_cls)
                for cpt_name in device_cls.component_names:
                    cpt = getattr(device_cls, cpt_name)
                    if hasattr(cpt, 'cls') and not cpt.lazy:
                        if issubclass(cpt.cls, desired_cls):
                            attrs.append([cpt_name])
                        subattrs = inspect_device_cls(cpt.cls, desired_cls,
                                                      cache)
                        expand_subattrs = [[cpt_name] + a for a in subattrs]
                        attrs.extend(expand_subattrs)
                if attrs:
                    logger.debug('Class %s has matching subdevices %s',
                                 device_cls, attrs)
                else:
                    logger.debug('Class %s has no matching subdevices',
                                 device_cls)
            cache[device_cls] = attrs
            return attrs

    for name, obj in scope_objs.items():
        # Determine whether or not to include this object
        include = False
        if cls == 'function':
            if isfunction(obj):
                include = True
        elif isinstance(obj, cls):
            include = True

        if include:
            logger.debug('Adding %s to %s namespace', name, cls)
            setattr(class_space, name, obj)

        # Determine whether or not to include any subdevices
        if isinstance(obj, Device):
            subdevice_attrs = inspect_device_cls(obj.__class__, cls, cache)
            for attrs in subdevice_attrs:
                device = obj
                for attr in attrs:
                    device = getattr(device, attr)
                logger.debug('Adding %s to %s namespace',
                             device.name, cls)
                setattr(class_space, device.name, device)

    return class_space


def tree_namespace(scope=None):
    """
    Create a ``namespace`` that accumulates objects and creates a tree.

    This tree is a nested set of `IterableNamespace` objects based on the
    object names as defined in scope. We will split on underscores and use the
    splits to create the tree.

    Parameters
    ----------
    scope: ``module``, ``namespace``, or ``list`` of these
        Every object attached to the given modules will be considered for the
        `tree_namespace`. If ``scope`` is omitted, we'll check all objects
        loaded by ``hutch-python`` and everything in the caller's global frame.

    Returns
    -------
    namespace: `IterableNamespace`
    """
    logger.debug('Create tree_namespace scope=%s', scope)
    scope_objs = extract_objs(scope=scope, stack_offset=1)

    def nested_defaultdict():
        return defaultdict(nested_defaultdict)

    tree_dict = nested_defaultdict()

    # Decide which nodes are objs, which are namespaces
    for name, obj in scope_objs.items():
        curr_dict = tree_dict
        keys = name.split('_')
        valid_keys = True
        for key in keys:
            if iskeyword(key):
                logger.warning('Issue in tree_namespace, %s in %s is a '
                               'reserved python keyword, omitting from tree',
                               key, name)
                valid_keys = False
                break
            if not key.isidentifier():
                logger.warning('Issue in tree_namespace, %s in %s is an '
                               'invalid python identifier, omitting from tree',
                               key, name)
                valid_keys = False
                break
        if valid_keys:
            for key in keys:
                curr_dict = curr_dict[key]
            curr_dict['_obj'] = obj

    # Unpack tree_dict to make tree_space
    def unpack_node(node):
        obj = node.pop('_obj', None)
        if obj is None:
            obj = IterableNamespace()
        for key, value in node.items():
            if hasattr(obj, key):
                # This means we would be overwriting something important
                logger.warning('Issue in tree_namespace, tried to overrwrite'
                               '%s.%s=%s', obj, key, getattr(obj, key))
            else:
                sub_node = unpack_node(value)
                try:
                    setattr(obj, key, sub_node)
                except AttributeError:
                    # This means that the object can't have attributes set
                    logger.warning('Object %r not a valid node, omitting '
                                   'from tree', obj)
                    obj = IterableNamespace()
                    setattr(obj, key, sub_node)
        return obj

    tree_space = unpack_node(tree_dict)
    logger.debug('Created tree namespace %s', tree_space)
    return tree_space
