"""
This module modifies an ``ipython`` shell to automatically close if it has been 
idle for a certain number of hours. If no command is entered in the ipython instance
for more than the maximum idle time, the session is automatically closed. The 
maximum idle time can be updated. Currently, it is set to 48 hours.
"""

import time
import sys, select
from IPython import get_ipython
from threading import Thread


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

    max_idle_time: int
        The maximum number of seconds a user session can be idle (currently set 
        to 172800 seconds or 48 hours).
    
    last_active_time: float
        The time of the last user activity in this session.

    idle_time: float
        The amount of time the user session has been idle.
    '''

    def __init__(self, ipython):
        self.curr_time = 0
        self.max_idle_time = 30  # 86400 is number of seconds in 24 hours
        self.last_active_time = 0
        self.idle_time = 0

        # _set_last_active_time() function will trigger every time user runs a cell
        ipython.events.register('post_run_cell', self._set_last_active_time)

    def _set_last_active_time(self, result):
        self.last_active_time = time.time()

    def _get_time_passed(self):
        self.curr_time = time.time()
        self.idle_time = self.curr_time - self.last_active_time

    def _timer(self, sleep_time):
        time.sleep(sleep_time)

    def _start_session(self):

        # Check if idle_time has exceeded max_idle_time
        while (self.idle_time < self.max_idle_time):            # 0 < 50
            self._timer(self.max_idle_time - self.idle_time)    # set timer to 50 sec
            self._get_time_passed()                             # 50 sec have passed

            if (self.idle_time >= self.max_idle_time):          # true
                print("This hutch-python session has been idle for 1 day and will automatically close in 24 hours. \nAny code that is currently running will continue to run until it is completed.\n If you would like to keep this session active longer, enter the number of hours here (max is 96): "))
                
                # Set a timeout for user input
                select.select([sys.stdin], [], [], 10)
                extend_hours = int(sys.stdin.readline())
                attempts = 0

                # Any data read by sys.stdin is of type string even if it's cast as int. 
                # But if the data is cast into int it, math operations can be perfomrmed on it.
                # Checking if extend_hours is int will evaluate to false, so checking if 
                # (extend_hours/2) is equal to an integer.

                while ((extend_hours/2) is not int and attempts < 4):
                    attempts += 1
                    print("An incorrect input was detect. Please enter the number of hours to extend this session: ")
                    select.select([sys.stdin], [], [], 10)
                    extend_hours = int(sys.stdin.readline())

                if (type(extend_hours/2) is int):
                    if (extend_hours > 96):
                        self.max_idle_time = 96  # (96 * 60 * 60)
                        print("This session will be extended for 96 more hours.")
                    else:
                        self.max_idle_time = int(extend_hours)  # (extend_hours * 60 * 60)
                        print("This session will be extended for %d more hours." % extend_hours)
                else:
                    print("The number of hours was not entered. This session will close. Any code that is currently\n running will continue to run until it is completed (to see results\n in the console please do not close this window).")

        # Close this ipython session
        get_ipython().ask_exit()


def load_ipython_extension(ipython):
    """
    Initialize the `IPythonSessionTimer`.

    This starts a timer that checks if the user session has been 
    idle for 48 hours or longer. If so, close the user session.

    Parameters
    ----------
    ip: ``ipython`` ``Shell``
        The active ``ipython`` ``Shell``, perhaps the one returned by
        ``IPython.get_ipython()``.
    """
    UserSessionTimer = IPythonSessionTimer(ipython)
    t1 = Thread(target=UserSessionTimer._start_session, daemon=True)
    t1.start()
