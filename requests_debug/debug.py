from requests import sessions
from time import time
import logging
import urllib
import threading
import simpleflake
import traceback

LOG = logging.getLogger(__name__)
__LOCALS = threading.local()

###############################################################################
## Public API
###############################################################################

def install_hook(thread_local=__LOCALS):
    """
    Install the hook into the requests library
    """
    # clear out any existing hooks
    uninstall_hook(thread_local=thread_local)
    # checkpoint the items
    checkpoint(thread_local=thread_local)
    # install the patch
    __patch_session(thread_local)


def checkpoint(thread_local=__LOCALS):
    """
    Reset the checkpoint
    """
    thread_local.checkpoint_id = simpleflake.simpleflake()


def clear_items(thread_local=__LOCALS):
    """
    clear the items
    """
    thread_local.items = []


def checkpoint_id(thread_local=__LOCALS):
    """
    Return the id for the current checkpoint
    """
    return __ensure_attr(thread_local, "checkpoint_id", simpleflake.simpleflake)


def items(thread_local=__LOCALS):
    """
    Return the items
    """
    return __ensure_attr(thread_local, "items", list)


def uninstall_hook(thread_local=__LOCALS):
    """
    Remove the hook from the requests library
    """
    if getattr(sessions, "_requests_debug_on", False):
        clear_items(thread_local=thread_local)
        reload(sessions)


###############################################################################
## Internal
###############################################################################
def __ensure_attr(obj, attr, default_cb):
    if not hasattr(obj, attr):
        setattr(obj, attr, default_cb())
    return getattr(obj, attr)


def __patch_session(thread_local):
    def decor(func):
        def inner(self, method, url, params=None, *args, **kwargs):
            __ensure_attr(thread_local, "items", list)
            __ensure_attr(thread_local, "checkpoint_id", simpleflake.simpleflake)

            if params:
                qs = urllib.urlencode(params)
                full_url = url + "?" + qs
            else:
                full_url = url

            
            start = time()
            status = None

            # initialize the data
            data ={"time_float": None,
                   "time": None,
                   "method": method,
                   "url": full_url,
                   "checkpoint_id": thread_local.checkpoint_id,
                   "exception": None,
                   "status": None}
            # insert the initial data, we'll mutate it on completion
            thread_local.items.append(data)
            
            try:
                response = func(self, method, url, params=params, *args, **kwargs)
                data['status'] = response.status_code
                return response
            except Exception, e:
                LOG.exception("Error Making Request %s %s checkpoint=%s", method,
                              full_url, data['checkpoint_id'])
                data['exception'] = traceback.format_exc()
                raise
            finally:
                end = time()
                duration = end - start
                data['time_float'] = duration
                data['time'] = "%.3f" % duration,
                LOG.debug("%s %s %.4f checkpoint=%s", 
                          method, full_url, duration, data['checkpoint_id'], 
                          extra=data)

        return inner

    sessions._requests_debug_on = True
    sessions.Session.request = decor(sessions.Session.request)

