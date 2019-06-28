# -*- coding: utf-8 -*-
"""Module for errors shared among pynag.Parsers package."""

from __future__ import absolute_import
import pynag.errors


class ParserError(pynag.errors.PynagError):
    """ ParserError is used for errors that the Parser has when parsing config.

    Typical usecase when there is a critical error while trying to read configuration.
    """
    filename = None
    line_start = None
    message = None

    def __init__(self, message=None, item=None):
        """ Creates an instance of ParserError

        Args:

            message: Message to be printed by the error

            item: Pynag item who caused the error

        """
        self.message = message
        if item is None:
            return
        self.item = item
        self.filename = item['meta']['filename']
        self.line_start = item['meta'].get('line_start')

    def __str__(self):
        message = self.message
        if self.filename and self.line_start:
            message = '%s in %s, line %s' % (message, self.filename, self.line_start)
        return repr(message)
