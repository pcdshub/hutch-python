import logging
from types import SimpleNamespace

from ophyd.device import Device, Component
from ophyd.signal import Signal

from hutch_python.namespace import class_namespace, tree_namespace


logger = logging.getLogger(__name__)


def test_class_namespace():
    logger.debug('test_class_namespace')
    scope = SimpleNamespace(one=1, two=2.0, three='3', four=lambda x: 4)
    int_space = class_namespace(int, scope)
    float_space = class_namespace(float, scope)
    str_space = class_namespace(str, scope)
    func_space = class_namespace('function', scope)
    err_space = class_namespace('erqwerasd', scope)
    assert int_space.one == 1
    assert float_space.two == 2.0
    assert str_space.three == '3'
    assert func_space.four(1) == 4
    assert len(err_space) == 0


class Layer(Device):
    potato = Component(Device)


class NormalDevice(Device):
    apples = Component(Device)
    bananas = Component(Device, lazy=True)
    oranges = Component(Signal)
    veggies = Component(Layer)


def test_class_namespace_subdevices():
    logger.debug('test_class_namespace_subdevices')
    scope = SimpleNamespace(tree=NormalDevice(name='tree'))
    device_space = class_namespace(Device, scope)
    assert isinstance(device_space.tree, NormalDevice)
    assert isinstance(device_space.tree_apples, Device)
    assert isinstance(device_space.tree_veggies, Layer)
    assert isinstance(device_space.tree_veggies_potato, Device)
    assert not hasattr(device_space, 'apples')
    assert not hasattr(device_space, 'bananas')
    assert not hasattr(device_space, 'tree_bananas')
    assert not hasattr(device_space, 'oranges')
    assert not hasattr(device_space, 'tree_oranges')


def test_tree_namespace():
    logger.debug('test_metadata_namespace')
    scope = SimpleNamespace(mfx_dia_obj1=1, mfx_dia_obj2=2,
                            mfx_dg2_obj3=3, mfx_obj4=4,
                            xpp_sb2_obj5=5)
    namespaces = tree_namespace(scope=scope)
    mfx = namespaces.mfx
    xpp = namespaces.xpp
    assert mfx.dia.obj1 == 1
    assert mfx.dia.obj2 == 2
    assert mfx.dg2.obj3 == 3
    assert mfx.obj4 == 4
    assert xpp.sb2.obj5 == 5


def test_same_name():
    logger.debug('test_same_name')
    # This should be ok, but make sure the warning is covered
    scope = SimpleNamespace(hutch_stand=SimpleNamespace(dev=1),
                            hutch_stand_dev=2)
    tree_namespace(scope=scope)


def test_conflicting_name():
    logger.debug('test_conflicting_name')
    # There was a bug where names could conflict with eachother
    scope = SimpleNamespace(daq=Signal(name='daq'),
                            daq_repeat_echo='daq_repeat_echo',
                            daq_repeat=Signal(name='daq_repeat'),
                            daq_deep='daq_deep',
                            daq_deep_deep=Signal(name='daq_deep_deep'))
    ns = tree_namespace(scope=scope)
    assert ns.daq.name == 'daq'
    assert ns.daq.repeat.echo == 'daq_repeat_echo'
    assert ns.daq.repeat.name == 'daq_repeat'
