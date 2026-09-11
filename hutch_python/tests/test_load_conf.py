import logging
import os.path
from socket import gethostname
from types import SimpleNamespace

import pytest
from pcdsdaq.daq import Daq
from pcdsdaq.sim import set_sim_mode
from pcdsdaq.sim.pydaq import Control as SimControl
from pcdsdevices.interface import Presets

import hutch_python.qs_load
from hutch_python.load_conf import load, load_conf

from .conftest import (TST_CAM_CFG, BlueskyScan, ELog, QSBackend, lightpath,
                       requires_elog, requires_psdaq, skip_if_win32_generic,
                       skip_if_win32_pcdsdaq)

logger = logging.getLogger(__name__)


@skip_if_win32_pcdsdaq
def test_file_load():
    logger.debug('test_file_load')
    set_sim_mode(True)
    objs = load(os.path.join(os.path.dirname(__file__), 'conf.yaml'))
    should_have = ('x', 'unique_device', 'calc_thing', 'daq', 'scan_pvs')
    if lightpath is not None:
        should_have += ('tst_beampath',)
    err = '{} was overriden by a namespace'
    for elem in should_have:
        assert not isinstance(objs[elem], SimpleNamespace), err.format(elem)
    assert 'tst' not in objs  # Tree namespace should be disabled
    assert len(Presets._paths) == 2


def test_experiment_presets_disabled(monkeypatch, tmp_path):
    # Check that an active experiment doesn't allow experiment presets to
    # be configured when the setting is disabled.
    setup_calls = []

    def mock_setup_preset_paths(**kwargs):
        setup_calls.append(kwargs)
    monkeypatch.setattr(
        'hutch_python.load_conf.setup_preset_paths',
        mock_setup_preset_paths,
    )
    monkeypatch.setattr(
        'hutch_python.load_conf.get_qs_objs',
        lambda expname: {},
    )
    monkeypatch.setattr(
        'hutch_python.load_conf.get_exp_objs',
        lambda expname: SimpleNamespace(),
    )
    load_conf(
        {
            'hutch': 'tst',
            'experiment': 'tstx010',
            'load_experiment_presets': False,
            'daq_type': 'nodaq',
        },
        hutch_dir=tmp_path,
    )
    beamline_path = tmp_path / 'presets' / 'beamline'
    experiment_path = tmp_path / 'presets' / 'x010'
    assert setup_calls == [{
        'hutch': beamline_path,
        'defer_loading': True,
    }]
    assert beamline_path.is_dir()
    assert not experiment_path.exists()


def test_presets_without_experiment(monkeypatch, tmp_path):
    setup_calls = []
    monkeypatch.setattr(
        'hutch_python.load_conf.setup_preset_paths',
        lambda **kwargs: setup_calls.append(kwargs),
    )
    load_conf(
        {
            'load_experiment_presets': True,
            'daq_type': 'nodaq',
        },
        hutch_dir=tmp_path,
    )
    assert setup_calls == [{
        'hutch': tmp_path / 'presets' / 'beamline',
        'defer_loading': True,
    }]


def test_exp_override():
    logger.debug('test_exp_override')
    set_sim_mode(True)
    # Should work with or without hutch name
    objs = load(os.path.join(os.path.dirname(__file__), 'conf.yaml'),
                SimpleNamespace(exp='x011'))
    assert hasattr(objs['x'], 'cats')
    objs = load(os.path.join(os.path.dirname(__file__), 'conf.yaml'),
                SimpleNamespace(exp='tstx011'))
    assert hasattr(objs['x'], 'cats')


def test_no_file():
    logger.debug('test_no_file')
    objs = load()
    assert len(objs) > 1


def test_conf_empty():
    logger.debug('test_conf_empty')
    objs = load_conf({})
    assert len(objs) > 1


@requires_elog
def test_elog(monkeypatch, temporary_config):
    logger.debug('test_elog')
    monkeypatch.setattr(hutch_python.load_conf, 'HutchELog', ELog)
    # No platform
    objs = load_conf({'hutch': 'TST'})
    assert objs['elog'].station is None
    # Check authentication worked correctly
    assert objs['elog'].user == 'user'
    assert objs['elog'].pw == 'pw'
    # Define default platform
    objs = load_conf({'daq_platform': {'default': 1},
                      'hutch': 'TST'})
    assert objs['elog'].station is None
    # Define host platform
    hostname = gethostname()
    objs = load_conf({'daq_platform': {'default': 3,
                                       hostname: 4},
                      'hutch': 'TST'})
    assert objs['elog'].station == '1'


@requires_psdaq
def test_lcls2_daq_config(dummy_zmq_lcls2):
    logger.debug('test_lcls2_daq')

    host = 'fake-hostname-drp'
    platform = 1
    config = {
        'daq_type': 'lcls2',
        'daq_host': host,
        'daq_platform': {'default': platform},
    }
    objs = load_conf(config)
    daq = objs['daq']
    assert isinstance(daq, BlueskyScan)
    assert daq.control.host == host
    assert daq.control.platform == platform


@skip_if_win32_pcdsdaq
def test_simdaq_config():
    logger.debug('test_simdaq_config')
    objs = load_conf({'daq_type': 'lcls1-sim'})
    daq = objs['daq']
    assert isinstance(daq, Daq)
    daq.connect()
    assert isinstance(daq._control, SimControl)


def test_nodaq_config():
    logger.debug('test_nodaq_config')
    objs = load_conf({'daq_type': 'nodaq'})
    with pytest.raises(KeyError):
        objs['daq']


def test_camviewer_load(monkeypatch):
    logger.debug('test_camviewer_load')
    monkeypatch.setattr(hutch_python.load_conf, 'CAMVIEWER_CFG', TST_CAM_CFG)
    objs = load_conf({'hutch': ''})
    assert 'camviewer' in objs
    assert 'my_cam' in dir(objs['camviewer'])


def test_skip_failures():
    logger.debug('test_skip_failures')
    # Should not raise
    load_conf(dict(hutch=345243, db=12351324, experiment=2341234, load=123454,
                   bananas='dole'))


@skip_if_win32_generic
def test_auto_experiment(fake_curexp_script):
    logger.debug('test_auto_experiment')
    hutch_python.qs_load.QSBackend = QSBackend
    objs = load_conf(dict(hutch='tst'))
    assert objs['inj_x'].run == '15'
    assert objs['inj_x'].proposal == 'LR12'
    assert objs['x'].inj_x == objs['inj_x']


def test_cannot_auto():
    logger.debug('test_cannot_auto')
    # Fail silently
    load_conf(dict(hutch='tst'))
