"""
This module is used to both gather and report information for the purpose of
identifying bugs
"""
import getpass
import logging
import os
import subprocess
import tempfile
import textwrap
import warnings
from configparser import ConfigParser, NoOptionError, NoSectionError

import requests
import simplejson
from IPython.core.history import HistoryAccessor
from IPython.core.magic import Magics, line_magic, magics_class
from IPython.utils.io import capture_output
from jinja2 import Environment, PackageLoader

from .log_setup import get_session_logfiles

logger = logging.getLogger(__name__)


# This function is aliased here so it can be easily be patched by the test
# suite. This allows us to eloquently simulate user inputted data
request_input = input


def get_current_environment():
    """
    Get the current CONDA environment

    The environment name is gathered by first checking environment variable
    ``$CONDA_ENVNAME`` that is set by the hutch-python startup scripts. If for
    whatever reason that is not available we check ``$CONDA_DEFAULT_ENV`` which
    is set by Conda itself. The reason this is not relied on primarily is it
    has a strange name and is entirely undocumented but seems to work
    effectively.

    In addition the hutch-python startup script sets the ``PYTHONPATH`` to pick
    up packages in "development" mode. The list of package names installed this
    way is found to help inform how the current Python environment differs from
    the enforced CONDA environment

    Returns
    -------
    env: str
        Name of environment

    dev_pkgs :list
        List of packages installed in the development folder
    """
    # Search for the environment variable set by the hutch python setup
    env = os.getenv('CONDA_ENVNAME')
    # Otherwise look for built-in Conda environment variables
    if not env:
        env = os.getenv('CONDA_DEFAULT_ENV')
    # Check the top level PYTHONPATH to see if we have packages installed in
    # development mode
    dev = os.getenv('PYTHONPATH')
    if dev:
        try:
            dev_pkgs = os.listdir(dev)
        except FileNotFoundError:
            logger.debug("No dev folder found")
            dev_pkgs = list()
    else:
        dev_pkgs = list()
    return env, dev_pkgs


def get_last_n_commands(n):
    """
    Find the last n commands entered in the IPython session

    Parameters
    ----------
    n : int
        Number of commands to retrieve

    Returns
    -------
    commands : str
        Block of text representing user input
    """
    # Ignore warnings generated by the HistoryAccessor. This can be removed
    # when https://github.com/ipython/ipython/pull/11054 reaches our release
    # environment
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', UserWarning)
        ha = HistoryAccessor()
    # Parse the last n commands of the IPython history, joining printed
    # messages
    return '\n'.join([cmd[2] for cmd in ha.get_tail(n, include_latest=True)])


def get_text_from_editor():
    """
    Request a description written in a text editor

    Opens a vim session with a prompt to request a detailed response from the
    operator.

    Returns
    -------
    text : str
        Block of text of the user input
    """
    with tempfile.NamedTemporaryFile(suffix='.tmp', mode='w+t') as f:
        # Create a temporary file with instructions on describing bug
        f.write(message + '\n\n')
        f.flush()
        # Open the editor and allow the user to type
        editor = os.environ.get('EDITOR', 'vim')
        subprocess.call([editor, f.name])
        # Read and clean the file
        f.seek(0)
        text = ''.join([line.lstrip() for line in f.readlines()
                        if line and not line.lstrip().startswith('#')])
        return '\n'.join(textwrap.wrap(text, width=100))


def report_bug(title=None, description=None, author=None,
               prior_commands=None, captured_output=None, **kwargs):
    """
    Report a bug from the IPython session

    The purpose of this command is to collect the necessary information to
    later help diagnose and troubleshoot the issue. This is written as an
    interactive tool, but it can be used in a non-interactive way by entering
    the information on the call.

    By the end we should have gathered:

        * A brief description of the problem
        * The relevant commands to the bug report
        * Name of the current CONDA environment
        * Any packages installed in "development" mode
        * Relevant logfiles
        * Name of bug report author

    Parameters
    ----------
    title : str, optional
        One sentence description of the issue

    description : str, optional
        Written description of problem. If this is not provided, a text editor
        is launched that request the information from the user

    author : str, optional
        Name of bug report author. If not provided, this is requested from the
        user via command line

    prior_commands : int, optional
        Number of prior commands to capture. If this is not provided, this is
        requested from the user via command line.

    captured_output : str, optional
        Captured output from the command

    kwargs:
        Pass authentication information to :func:`.post_to_github`
    """
    logger.debug("Reporting a bug from the IPython terminal ...")
    if not title:
        title = request_input('Please provide a one sentence description of '
                              'the problem you are encountering: ')
    # Grab relevant commands
    if not prior_commands:
        try:
            n = request_input("How many of the previous commands are relevant "
                              "to the issue you would like investigated?: ")
            prior_commands = int(n)
        except ValueError:
            logger.error("Invalid input %s", n)
            # Only select the last command by default
            prior_commands = 1
    # Grab specified number of commands
    try:
        commands = get_last_n_commands(prior_commands)
    # If the user somehow has no IPython history this is raised. A very rare
    # occurence except for in Continuous Integration tests
    except OSError:
        logger.exception('Unable to retrieve commmands from the '
                         'IPython session')
        commands = ''
    # Get a more specific description
    description = description or get_text_from_editor()
    # Find the author
    if not author:
        author = request_input('Please enter a name so we can follow-up with '
                               'additional questions: ')
        author = author or getpass.getuser()
    # Gather environment information
    conda_env, dev_pkgs = get_current_environment()
    # Gather logfiles
    logfiles = get_session_logfiles()
    # Save the report to JSON
    return post_to_github({'title': title, 'author': author,
                           'commands': commands, 'description': description,
                           'env': conda_env, 'logfiles': logfiles,
                           'output': captured_output, 'dev_pkgs': dev_pkgs},
                          **kwargs)


def post_to_github(report, user=None, pw=None, proxies=None):
    """
    Post an issue report to GitHub

    Authentication can be done in three different ways depending on preference.
    First, the call can be made with the username and password specified. If
    this is not done we first look for a configuration file web.cfg that has
    a section labeled GitHub which looks like:

    .. code:: ini

        [GITHUB]
        user=username
        pw=password
        proxy=http://proxyhost:port

    If this is not available the username and password will be requested via
    the command line. The proxy specification allows posts from hosts without
    direct connection to the internet. Please consult PCDS for information
    about available hosts and ports.

    Parameters
    ----------
    report: dict
        A report dictionary with keys:

            * title
            * author
            * commands
            * description
            * env
            * logfiles
            * output
            * dev_pkgs

    user: str, optional
        Username of GitHub profile.

    pw : str, optional
        Password for GitHub profile. This will be queried for if not provided
        in the function call.

    proxies : dict, optional
        Mapping of protocol to hostname and port.
    """
    proxies = proxies or dict()
    # Determine authentication method. No username or password search for
    # configuration file with GITHUB section
    if not user and not pw:
        # Find configuration file
        cfg = ConfigParser()
        cfgs = cfg.read(['web.cfg', '.web.cfg',
                         os.path.expanduser('~/.web.cfg'),
                         'qs.cfg', '.qs.cfg',
                         os.path.expanduser('~/.qs.cfg')])
        if cfgs:
            # Grab login information
            try:
                user = cfg.get('GITHUB', 'user')
                pw = cfg.get('GITHUB', 'pw')
            except (NoOptionError, NoSectionError):
                logger.debug('No GITHUB section in configuration file '
                             'with user and pw entries')
            # Grab proxy information if we will be using web.cfg
            if (user or pw) and not proxies:
                try:
                    proxy_name = cfg.get('GITHUB', 'proxy')
                    logger.debug("Using proxy host %s", proxy_name)
                    proxies = {'https': proxy_name}
                except NoOptionError:
                    logger.debug("No proxy information found")
        # No valid configurations
        else:
            logger.debug('No "web.cfg" file found')
    # Manually ask if we didn't get the username or password already
    if not user:
        user = input('Github Username: ')
    if not pw:
        pw = getpass.getpass('Password for GitHub Account {}: '
                             ''.format(user))
    # Our url to create issues via POST
    url = 'https://api.github.com/repos/pcdshub/Bug-Reports/issues'
    # Create the body of the template
    env = Environment(loader=PackageLoader('hutch_python'),
                      trim_blocks=True, lstrip_blocks=True)
    template = env.get_template('issue.template')
    body = template.render(report)
    # Requests session
    session = requests.Session()
    session.auth = (user, pw)
    session.proxies.update(proxies)
    issue = {'title': report['title'],
             'body': body,
             'assignee': None,
             'milestone': None,
             'labels': []}  # TODO: Determine hutch to create issue for
    # Post to GitHub
    r = session.post(url, simplejson.dumps(issue))
    if r.status_code == 201:
        logger.info("Succesfully created GitHub issue")
    else:
        logger.exception("Could not create GitHub issue. HTTP Status Code: %s",
                         r.status_code)


@magics_class
class BugMagics(Magics):
    """Magics function for report_bug function"""

    @line_magic
    def report_bug(self, line):
        """Creates a bug_report while running the given line"""
        # Store the output of our command
        with capture_output() as shell_output:
            self.shell.run_cell(line)
        # Show the capture output to the user
        shell_output.show()
        # Create the report
        report_bug(prior_commands=1, captured_output=shell_output.stdout)


message = """\
# Please describe the issue you are wishing to report. What did you expect to
# happen? What actually happened? Does this issue occur every time you use this
# function?

# Lines that start with a '#' will be ignored. Save the session and exit to
# store the description. Press "i" to be begin typing, then "Esc" followed by
# ":wq" to exit.
"""


def load_ipython_extension(ipython):
    ipython.register_magics(BugMagics)
