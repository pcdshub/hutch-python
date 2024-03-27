import json
import logging
import os
from unittest.mock import patch

import happi
import pytest
from conftest import cli_args

from ..epics_arch import get_items, main, print_dry_run, update_file

logger = logging.getLogger(__name__)


def test_epics_arch_args():
    with cli_args(['epicsarch-qs', 'xpplv6818']):
        with patch('hutch_python.epics_arch.update_file') as mock:
            main()
        mock.assert_called_once()


@patch('hutch_python.epics_arch.update_file')
def test_update_file_with_hutch_args(create_mock):
    with cli_args(['epicsarch-qs', 'xpplv6818', '--hutch', 'xpp']):
        with patch('hutch_python.epics_arch.get_items', return_value=items):
            main()
        create_mock.assert_called_once()


@patch('hutch_python.epics_arch.update_file')
@patch('os.path.exists', return_value=True)
def test_update_file_with_path_args(path_mock, create_mock):
    with cli_args(['epicsarch-qs', 'xpplv6818', '--path', '/my/path/xpp/']):
        with patch('hutch_python.epics_arch.get_items', return_value=items):
            main()
        create_mock.assert_called_once()


@patch('os.path.exists', return_value=False)
def test_update_file_with_bad_path_args(path_mock):
    with cli_args(['epicsarch-qs', 'xpplv6818', '--path', '/my/path/xpp/']):
        with pytest.raises(OSError):
            main()


@patch('hutch_python.epics_arch.get_questionnaire_data')
def test_dry_run_args(get_data_mock, items):
    with cli_args(['epicsarch-qs', 'xpplv6818', '--dry-run']):
        with patch('hutch_python.epics_arch.get_items', return_value=items):
            with patch('hutch_python.epics_arch.print_dry_run') as mock:
                main()
            mock.assert_called_once()
            get_data_mock.assert_called_once


def test_dry_run_args_exception(fake_qsbackend):
    with pytest.raises(Exception):
        get_items('somebadname')


@pytest.mark.xfail
def test_print_dry_run(items, capsys):
    with patch('hutch_python.epics_arch.get_items', return_value=items):
        expected_list = ['*acromag', 'XPP:USR:ao1', '*lbl', 'XPP:USR:EVR:TRIG0', '*tape_x', 'XPP:LBL:MMN:04', '*transducer_y', 'XPP:LBL:MMN:05', '*xes_y', 'XPP:LBL:MMN:06']
        expected_str = ''
        for m in expected_list:
            expected_str += m + '\n'

        print_dry_run('xpplv6818')
        readout = capsys.readouterr()
        assert expected_str in readout


def test_update_file(items):
    dir_path = os.path.dirname(os.path.realpath(__file__)) + '/'
    with patch('hutch_python.epics_arch.get_items', return_value=items):
        update_file('tstlr3216', path=dir_path)
        expected_file = ''.join((dir_path, 'epicsArch_tstlr3216.txt'))
        expected_list = [
            '*acromag', 'XPP:USR:ao1', '*lbl', 'XPP:USR:EVR:TRIG0', '*tape_x', 'XPP:LBL:MMN:04', '*transducer_y',
            'XPP:LBL:MMN:05', '*xes_y', 'XPP:LBL:MMN:06',
        ]
        temp_list = [line.rstrip('\n') for line in open(expected_file)]
        # Check that the file was made
        assert os.path.exists(expected_file)
        assert temp_list == expected_list
        # Cleanup
        os.remove(expected_file)


def test_update_file_bad_path(items):
    with patch('hutch_python.epics_arch.get_items', return_value=items):
        with pytest.raises(OSError):
            update_file('tstlr3216', path='/some/bad/path/')


@pytest.fixture(scope='function')
def json_db(tmp_path_factory):
    dir_path = tmp_path_factory.mktemp("db_dir")
    json_path = dir_path / 'db.json'
    json_path.write_text(json.dumps(all_items))
    return str(json_path.absolute())


@pytest.fixture(scope='function')
def items(json_db):
    client = happi.client.Client(path=json_db)
    return client.all_items


all_items = json.loads("""{
            "tape_x": {
                "_id": "tape_x",
                "active": true,
                "args": ["{{prefix}}"],
                "beamline": "XPP",
                "kwargs": {"name": "{{name}}"},
                "lightpath": false,
                "name": "tape_x",
                "prefix": "XPP:LBL:MMN:04",
                "type": "pcdsdevices.happi.containers.LCLSItem",
                "location": "XPP goniometer",
                "purpose": "Tape X",
                "pvbase": "XPP:LBL:MMN:04",
                "stageidentity": "Newport"
                },
            "transducer_y": {
                "_id": "transducer_y",
                "active": true,
                "args": ["{{prefix}}"],
                "beamline": "XPP",
                "kwargs": {"name": "{{name}}"},
                "lightpath": false,
                "name": "transducer_y",
                "prefix": "XPP:LBL:MMN:05",
                "type": "pcdsdevices.happi.containers.LCLSItem",
                "location": "XPP goniometer",
                "purpose": "Transducer Y",
                "stageidentity": "Newport",
                "pvbase": "XPP:LBL:MMN:05"
                },
            "xes_y": {
                "_id": "xes_y",
                "active": true,
                "args": ["{{prefix}}"],
                "beamline": "XPP",
                "kwargs": {"name": "{{name}}"},
                "lightpath": false,
                "name": "xes_y",
                "prefix": "XPP:LBL:MMN:06",
                "type": "pcdsdevices.happi.containers.LCLSItem",
                "location": "XPP goniometer",
                "stageidentity": "Newport",
                "purpose": "Xes Epix Y",
                "pvbase": "XPP:LBL:MMN:06"
                },
            "lbl": {
                "_id": "lbl",
                "active": true,
                "args": ["{{prefix}}"],
                "beamline": "XPP",
                "kwargs": {"name": "{{name}}"},
                "lightpath": false,
                "name": "lbl",
                "prefix": "XPP:USR:EVR:TRIG0",
                "type": "pcdsdevices.happi.containers.LCLSItem",
                "purpose": "LBL",
                "width": "1e-5",
                "polarity": "positiv",
                "delay": "0.0008",
                "pvbase": "XPP:USR:EVR:TRIG0",
                "eventcode": "42"
                },
            "acromag": {
                "_id": "acromag",
                "active": true,
                "args": ["{{prefix}}"],
                "beamline": "XPP",
                "kwargs": {"name": "{{name}}"},
                "lightpath": false,
                "name": "acromag",
                "prefix": "XPP:USR:ao1",
                "type": "pcdsdevices.happi.containers.LCLSItem",
                "device": "Acromag IP231 16-bit",
                "pvbase": "XPP:USR:ao1",
                "purpose": "Evo Shutter 1",
                "channel": "6"
                }
                }
                """)
