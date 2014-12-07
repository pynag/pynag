"""Common decorators used throughout pynag."""

import threading

rlock = threading.RLock()


def synchronized(lock):
    """ Synchronization decorator

    Use this to make a multi-threaded method synchronized and thread-safe.

    Use the decorator like so::

        @pynag.Utils.synchronized(pynag.Utils.rlock)
    """
    def wrap(f):
        def newFunction(*args, **kw):
            lock.acquire()
            try:
                return f(*args, **kw)
            finally:
                lock.release()
        newFunction.__name__ = f.__name__
        newFunction.__module__ = f.__module__
        return newFunction
    return wrap


def cache_only(func):
    import pynag.Model
    def wrap(*args, **kwargs):
        pynag.Model.ObjectFetcher._cache_only = True
        try:
            return func(*args, **kwargs)
        finally:
            pynag.Model.ObjectFetcher._cache_only = False
    wrap.__name__ = func.__name__
    wrap.__module__ = func.__module__
    return wrap


