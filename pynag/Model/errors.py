import pynag.errors

class ModelError(pynag.errors.PynagError):
    """Base class for errors in this module."""


class InvalidMacro(ModelError):
    """Raised when a method is inputted with an invalid macro."""

