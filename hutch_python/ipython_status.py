"""
IPython plugin to print device.status() after showing the repr as Out in
interactive sessions
"""
import logging

logger = logging.getLogger(__name__)


class IPythonStatus:
    def __init__(self, ipython):
        self.In = ipython.user_ns['In']
        self.Out = ipython.user_ns['Out']

    def show_status(self):
        index = len(self.In) - 1
        if index in self.Out:
            obj = self.Out[index]
            if hasattr(obj, 'status'):
                try:
                    print(obj.status())
                except Exception:
                    err = 'Error showing device status'
                    logger.debug(err, exc_info=True)


def init_ipython_status(ip):
    ip.events.register('post_execute', IPythonStatus(ip).show_status)
