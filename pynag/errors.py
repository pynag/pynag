"""Pynag Errors."""


class PynagError(Exception):
    """Base class for Pynag Exceptions."""
    def __init__(self, message, errorcode=None, errorstring=None, *args, **kwargs):
        self.errorcode = errorcode
        self.message = message
        self.errorstring = errorstring
        try:
            super(self.__class__, self).__init__(message, *args, **kwargs)
        except TypeError:  # Python 2.4 is fail
            Exception.__init__(self, message, *args, **kwargs)
