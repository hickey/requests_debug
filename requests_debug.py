from requests import sessions
from time import time
import logging
import urllib
import threading

__version__ = '0.1'

LOG = logging.getLogger(__name__)
__LOCALS = threading.local()

###############################################################################
## Public API
###############################################################################

def install_hook():
    """
    Install the hook into the requests library
    """
    __LOCALS.items = []
    __patch_session(__LOCALS)


def clear_items():
    """
    clear the items
    """
    __LOCALS.items = []


def items():
    """
    Return the items
    """
    return getattr(__LOCALS, "items", [])


def uninstall_hook():
    """
    Remove the hook from the requests library
    """
    clear_items()
    reload(sessions)


###############################################################################
## Internal
###############################################################################
def __patch_session(thread_local):
    def decor(func):
        def inner(self, method, url, params=None, *args, **kwargs):
            if not hasattr(thread_local, "items"):
                thread_local.items = []

            if params:
                qs = urllib.urlencode(params)
                full_url = url + "?" + qs
            else:
                full_url = url

            
            start = time()
            response = None
            status = None
            
            try:
                response = func(self, method, url, params=params, *args, **kwargs)
                status = response.status_code
                return response
            except:
                LOG.exception("Error Making Request %s %s", method,
                                      full_url)
                raise
            finally:
                end = time()
                duration = end - start

                data ={"time_float": duration,
                       "time": "%.3f" % duration,
                       "method": method,
                       "url": full_url,
                       "status": status}

                thread_local.items.append(data)
                LOG.debug("%s %s %.4f", method, full_url, duration,
                                 extra=data)

        return inner

    sessions.Session.request = decor(sessions.Session.request)

