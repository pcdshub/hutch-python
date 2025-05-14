import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from string import Template

import IPython.core.completer
import pytest
from conftest import cli_args, restore_logging

import hutch_python.cli
from hutch_python.cli import (HutchPythonArgs, configure_ipython_session,
                              get_parser, main)
from hutch_python.load_conf import load

from .conftest import skip_if_win32_generic

logger = logging.getLogger(__name__)

CFG_PATH = Path(os.path.dirname(__file__)) / 'conf.yaml'
CFG = str(CFG_PATH)


@pytest.fixture(scope='function')
def no_ipython_launch(monkeypatch):
    def no_op(*args, **kwargs):
        pass
    monkeypatch.setattr(hutch_python.cli, 'start_ipython', no_op)


@skip_if_win32_generic
def test_main_normal(no_ipython_launch):
    logger.debug('test_main_normal')

    with cli_args(['hutch_python', '--cfg', CFG]):
        with restore_logging():
            main()


@skip_if_win32_generic
def test_main_no_args(no_ipython_launch):
    logger.debug('test_main_no_args')

    with cli_args(['hutch_python']):
        with restore_logging():
            main()


@skip_if_win32_generic
def test_debug_arg(no_ipython_launch):
    logger.debug('test_debug_arg')

    with cli_args(['hutch_python', '--cfg', CFG, '--debug']):
        with restore_logging():
            main()


@skip_if_win32_generic
def test_sim_arg(no_ipython_launch):
    logger.debug('test_sim_arg')

    with cli_args(['hutch_python', '--cfg', CFG, '--sim']):
        with restore_logging():
            main()


def test_create_arg():
    logger.debug('test_create_arg_dev')
    hutch = 'temp_create'
    # CLI invocation will create the hutch folder in the folder pytest was
    # called from.  We should check and clean that folder.
    test_dir = Path.cwd() / hutch
    if test_dir.exists():
        shutil.rmtree(test_dir)

    # Needs manual confirmation if we run with capture output on...
    with cli_args(['hutch_python', '--create', hutch]):
        with restore_logging():
            main()

    assert test_dir.exists()

    # Make sure conf.yml is valid
    load(str(test_dir / 'conf.yml'))
    shutil.rmtree(test_dir)


def run_hpy_and_exit(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "hutch_python"] + list(args),
        input="exit\n",
        universal_newlines=True,
        capture_output=True,
    )


@pytest.mark.timeout(30)
def test_hist_file_arg():
    logger.debug("test_hist_file_arg")
    test_hist_file = (CFG_PATH.parent / "history.sqlite").resolve()

    # Test that the sqlite file gets made
    # First, need to remove the file if it already exists
    if test_hist_file.exists():
        test_hist_file.unlink()

    # Run with the good arg and exit
    run_hpy_and_exit("--hist-file", str(test_hist_file))
    # Was the history file created?
    assert test_hist_file.exists()
    # Remove the file for future tests
    test_hist_file.unlink()
    assert not test_hist_file.exists()


@pytest.mark.timeout(30)
@pytest.mark.parametrize("filepath,", (
    (CFG_PATH.parent / "aesefiudh" / "history.sqlite").resolve(),
    ":memory:",
))
def test_no_hist_file(filepath):
    # With the bad hist file or memory we should still run ok with just a warning
    test_hist_file = (CFG_PATH.parent / "history.sqlite").resolve()
    run_hpy_and_exit("--hist-file", str(filepath))
    assert not test_hist_file.exists()


@pytest.mark.timeout(30)
def test_template_file(monkeypatch):
    # Exercise the template + check default usage
    # We can't actually write to the default default in a test context
    # But we can check what the config would be
    new_default = str(CFG_PATH.parent / "${USER}-history.sqlite")
    new_default_filled = Template(new_default).substitute({"USER": os.environ["USER"]})
    monkeypatch.setattr(
        hutch_python.cli,
        "DEFAULT_HISTFILE",
        new_default,
    )
    parser = get_parser()
    args = parser.parse_args(["--hist-file"], namespace=HutchPythonArgs())
    ipy_config = configure_ipython_session(args)
    assert ipy_config.HistoryManager.hist_file == new_default_filled


@skip_if_win32_generic
def test_run_script():
    logger.debug('test_run_script')

    # Will throw a name error unless we run the script inside the full env
    with cli_args(['hutch_python', '--cfg', CFG, '--debug',
                   str(Path(__file__).parent / 'script.py')]):
        with restore_logging():
            main()


def test_ipython_tab_completion():
    class MyTest:
        THIS_SHOULD_NOT_BE_THERE = None

        def __dir__(self):
            return ['foobar']

    ns = {'a': MyTest()}

    # Side-effect of the following is monkey-patching `dir2` to "fix" this for
    # us.
    hutch_python.cli.configure_ipython_session(HutchPythonArgs())

    completer = IPython.core.completer.IPCompleter(namespace=ns)
    completer.limit_to__all__ = False
    completer.line_buffer = "a."
    assert 'a.THIS_SHOULD_NOT_BE_THERE' not in completer.attr_matches('a.')
    assert completer.attr_matches('a.') == ['a.foobar']
