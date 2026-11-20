"""
This module modifies an ``ipython`` shell to log inputs, outputs, and
tracebacks to a custom ``logger.input`` level. The ``INPUT`` level is lower
than the ``DEBUG`` level to avoid a terminal echo in debug mode.
"""
import functools
import logging
import sys
import textwrap
import threading
import traceback
import types

from .constants import INPUT_LEVEL
from .log_setup import log_exception_to_central_server

logger = logging.getLogger(__name__)
logger.input = functools.partial(logger.log, INPUT_LEVEL)
logger.setLevel(INPUT_LEVEL)

_ip_logger = None

EXCEPTION_MESSAGE_FOR_LOG_FILE = """\
Exception in IPython session%s. Last input line %s:
%s

Exception details:
%s
""".rstrip()


def _log_errors(func):
    """Decorator: wrap ``func`` to log exceptions."""

    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            logger.input('Logging error', exc_info=True)
    return wrapped


def _get_file_and_line_from_traceback(
    tb: types.TracebackType,
    *,
    on_error: str = "unknown"
) -> tuple[str, int]:
    """
    Get the last source filename and line number from the traceback.

    Parameters
    ----------
    tb : traceback
    on_error : str, optional
        The default filename if unable to determine the source code location
        from the traceback.

    Returns
    -------
    filename : str
    lineno : int
    """
    try:
        last_frame, exc_line = tuple(traceback.walk_tb(tb))[-1]
        return (last_frame.f_code.co_filename, exc_line)
    except Exception:
        return (on_error, 0)


_indented = functools.partial(textwrap.indent, prefix=' ' * 4)


class IPythonLogger:
    """
    Class that logs the most recent inputs, outputs, and exceptions at the
    custom ``INPUT`` level.

    Parameters
    ----------
    ipython : ``IPython.terminal.interactiveshell.TerminalInteractiveShell``
        The active ``ipython`` ``Shell``, perhaps the one returned by
        ``IPython.get_ipython()``.

    Attributes
    ----------
    ipython_in : list of str
        The IPython user input list.

    prev_err_value : Exception or None
        The last exception value that was logged.  Used for exception
        deduplication.

    line_in_progress : bool
        True if a line is currently in the process of being evaluated.
    """
    def __init__(self, ipython):
        self.ipython = ipython
        self.ipython_in = ipython.user_ns["In"]
        self.prev_err_value = None
        self.line_in_progress = False

        logging.addLevelName('INPUT', INPUT_LEVEL)

        ipython.events.register('pre_run_cell', self.log_user_input)
        ipython.events.register('post_run_cell', self.log_output)

        self._orig_sys_excepthook = sys.excepthook
        sys.excepthook = self._sys_exception_hook

        if hasattr(threading, "excepthook"):
            self._orig_thread_excepthook = threading.excepthook
            threading.excepthook = self._thread_excepthook

    def _should_log(self, exc_value):
        """Should the given exception be logged?"""
        return (
            isinstance(exc_value, Exception) and
            exc_value != self.prev_err_value
        )

    @_log_errors
    def _sys_exception_hook(self, exc_type, exc_value, exc_tb):
        """Unhandled exception hook - outside of input-related ones."""
        try:
            if self._should_log(exc_value):
                self._log_exception(
                    (exc_type, exc_value, exc_tb),
                    background=True
                )
        except Exception:
            ...
        return self._orig_sys_excepthook(exc_type, exc_value, exc_tb)

    @_log_errors
    def _thread_excepthook(self, args):
        """Unhandled exception in thread hook."""
        try:
            if self._should_log(args.exc_value):
                self._log_exception(
                    (args.exc_type, args.exc_value, args.exc_traceback),
                    background=True, thread=args.thread
                )
        except Exception:
            ...
        return self._orig_thread_excepthook(args)

    @_log_errors
    def log_user_input(self, info):
        """Logs the most recent input by way of the 'pre_run_cell' hook."""
        self.line_in_progress = True
        line_num = len(self.ipython_in)
        logger.input('In  [%d]: %s', line_num, info.raw_cell)

    @_log_errors
    def _log_exception(
        self, exc_info, line_input="", background=False, thread=None
    ):
        """
        Logs the given exception.

        Parameters
        ----------
        exc_info : (type, value, traceback)
            The exception information.

        line_input: str, optional
            The user input associated with the given line, if available.

        background : bool, optional
            Set if the exception happened in the background as part of an
            exception hook external to IPython.

        thread : threading.Thread, optional
            The associated thread when not the main thread, if available.
        """
        exc_type, exc_value, exc_traceback = exc_info
        try:
            line_num = len(self.ipython_in) - 1
            line_traceback = ''.join(traceback.format_exception(*exc_info))
            exc_file, exc_line = _get_file_and_line_from_traceback(
                exc_traceback
            )

            logger.input(
                EXCEPTION_MESSAGE_FOR_LOG_FILE,
                thread,
                line_num,
                _indented(line_input),
                _indented(line_traceback),
            )

            if not thread:
                message = f"In [{line_num}]: {line_input}"
            else:
                last_input = self.ipython_in[-1] if self.ipython_in else ""
                message = "\n".join(
                    (
                        f"Thread: {thread.name}",
                        f"Last user input [{line_num}]: {last_input}",
                    )
                )

            full_message = "\n".join(
                (
                    message,
                    f"Exception: {exc_type.__name__}: {exc_value}",
                    f"File: {exc_file} line {exc_line}",
                ),
            )

            log_exception_to_central_server(
                exc_info, stacklevel=2, message=full_message
            )
        finally:
            self.prev_err_value = exc_value

    @_log_errors
    def log_exception(self, line_input="[n/a]"):
        """Logs the most recent unhandled exception."""
        # These three ``sys.last_*`` variables are not always defined; they are
        # set when an exception is not handled and the interpreter prints an
        # error message and a stack traceback.

        last_value = getattr(sys, "last_value", None)
        if not last_value or not isinstance(last_value, Exception):
            # No exception to log, or ignore non-exception types
            return

        exc_info = (sys.last_type, last_value, sys.last_traceback)
        self._log_exception(exc_info, line_input=line_input)

    @_log_errors
    def log_output(self, result):
        """Logs the most recent output by way of the 'post_run_cell' hook."""
        self.line_in_progress = False
        if result.result:
            # Convert to string, limit to max tweet length
            line_num = len(self.ipython_in) - 1
            last_out = str(result.result)[:280]
            logger.input('Out [%d]: %s', line_num, last_out)

        if result.error_in_exec is not None:
            self.log_exception(result.info.raw_cell)


def load_ipython_extension(ipython):
    """
    Initialize the `IPythonLogger`.

    This involves adding the ``INPUT`` log level and registering
    ``IPythonLogger.log`` to run on the ``post-execute`` event.

    Parameters
    ----------
    ip: ``ipython`` ``Shell``
        The active ``ipython`` ``Shell``, perhaps the one returned by
        ``IPython.get_ipython()``.
    """
    global _ip_logger
    _ip_logger = IPythonLogger(ipython)
