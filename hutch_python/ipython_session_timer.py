"""
This module modifies an ``ipython`` shell to automatically close if it has been
idle for a certain number of hours. Each hutch can configure their conf.yml
file to set a timeout duration. The default duration is 48 hours.
"""

import time
from threading import Thread

max_idle_time = 172800.0  # number of seconds in 48 hours


def configure_timeout(session_timer):
    global max_idle_time
    if isinstance(session_timer, int) and session_timer > 0:
        max_idle_time = session_timer


class IPythonSessionTimer:
    '''
    Class tracks the amount of time the current `InteractiveShell` instance (henceforth
    called 'user session') has been idle and closes the session if more than 48
    hours have passed.

    Time is in seconds (floating point) since the epoch began. (In UNIX the
    epoch started on January 1, 1970, 00:00:00 UTC)

    Parameters
    ----------
    ipython : ``IPython.terminal.interactiveshell.TerminalInteractiveShell``
        The active ``ipython`` ``Shell``, perhaps the one returned by
        ``IPython.get_ipython()``.

    Attributes
    ----------
    curr_time: float
        The current time in seconds.

    max_idle_time: float
        The maximum number of seconds a user session can be idle (default is
        172800.0 seconds or 48 hours).

    last_active_time: float
        The time of the last user activity in this session.

    idle_time: float
        The amount of time the user session has been idle.
    '''

    def __init__(self, ipython):
        self.curr_time = 0.0
        self.max_idle_time = max_idle_time
        self.last_active_time = 0.0
        self.idle_time = 0.0
        self.user_active = False
        self.ip = ipython

        ipython.events.register('pre_run_cell', self._set_user_active)
        ipython.events.register('post_run_cell', self._set_user_inactive)

    def _set_user_active(self, *args, **kwargs):
        self.user_active = True
        self.last_active_time = time.monotonic()

    def _set_user_inactive(self, *args, **kwargs):
        self.user_active = False
        self.last_active_time = time.monotonic()

    def _set_idle_time(self):
        self.curr_time = time.monotonic()
        self.idle_time = self.curr_time - self.last_active_time

    def _start_session(self):
        # Check if idle_time has exceeded max_idle_time or if user is currently active
        while (self.idle_time < self.max_idle_time) or self.user_active:

            # Check if user is active once every minute
            while (self.user_active):
                time.sleep(60)
                self.idle_time = 0

            time.sleep(self.max_idle_time - self.idle_time)
            self._set_idle_time()

        # End the IPython session
        print("This hutch-python session has timed out. Please start a new session.")

        self.ip.ask_exit()
        self.ip.pt_app.app.exit()


def load_ipython_extension(ipython):
    """
    Initialize the `IPythonSessionTimer`.

    This starts a timer that checks if the user session has been
    idle for 48 hours or longer. If so, close the user session.

    Parameters
    ----------
    ipython: IPython.terminal.interactiveshell.TerminalInteractiveShell
        The active ``ipython`` ``Shell``, the one returned by
        ``IPython.get_ipython()``.
    """
    user_session_timer = IPythonSessionTimer(ipython)
    t1 = Thread(target=user_session_timer._start_session, daemon=True)
    t1.start()
