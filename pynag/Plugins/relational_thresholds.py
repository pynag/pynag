# -*- coding: utf-8 -*-
"""This module adds support for specifying thresholds by using relational operators

Examples:
disk_usage < 90%
"""
from pynag import errors
from pynag.Utils import metrics


EQ = '=='
LE = '<='
GE = '>='
NE = '!='
LT = '<'
GT = '>'
EQ2 = '='
NE2 = '<>'

OPERATORS = (GE, LE, NE, EQ, LT, GT, EQ2, NE2)


class Error(errors.PynagError):
    """Base class for errors in this module."""


class InvalidThreshold(Error):
    """Raised when parsing a threshold with invalid syntax."""


class NotSupported(Error):
    """Raised when when using a valid operator that we have not implemented."""


def parse_expression(expression):
    """

    Args:
    expression: str. Example: 'usage < 90'

    Returns:
        Tuple of: ('metric_name, 'operator, 'value', 'uom')

    Examples:
        >>> parse_expression('disk_usage > 90%')
        ('disk_usage', '>', '90', '%')
        >>> parse_expression('disk_usage >= 90%')
        ('disk_usage', '>=', '90', '%')
        >>> parse_expression('disk_usage FOO 90%')
        Traceback (most recent call last):
          ...
        ValueError: Expression needs to contain at least on of ('>=', '<=', '!=', '==', '<', '>', '=', '<>')
    """
    for operator in OPERATORS:
        if operator in expression:
            metric, value = expression.split(operator)
            metric = metric.strip()
            value = value.strip()
            value, uom = metrics.split_value_and_uom(value=value)
            break
    else:
        raise InvalidThreshold('Expression needs to contain at least on of %s' % (OPERATORS,))

    return metric, operator, value, uom


def check_threshold(left, operator, right):
    """
    :param left:
    :param operator:
    :param right:
    :return:

    Examples:
        >>> check_threshold(2, '>=', 1)
        True
        >>> check_threshold(2, '>=', 2)
        True
        >>> check_threshold(2, '>=', 3)
        False
        >>> check_threshold(2, '<=', 1)
        False
        >>> check_threshold(2, '<=', 2)
        True
        >>> check_threshold(2, '<=', 3)
        True
        >>> check_threshold(2, '<', 1)
        False
        >>> check_threshold(2, '<', 2)
        False
        >>> check_threshold(2, '<', 3)
        True
        >>> check_threshold(2, '>', 1)
        True
        >>> check_threshold(2, '>', 2)
        False
        >>> check_threshold(2, '>', 3)
        False
        >>> check_threshold(2, '==', 1)
        False
        >>> check_threshold(2, '==', 2)
        True
        >>> check_threshold(2, '!=', 1)
        True
        >>> check_threshold(2, '!=', 2)
        False
        >>> check_threshold(1,'foo', 1)
        Traceback (most recent call last):
          ...
        InvalidThreshold: Invalid operator "foo", needs to be one of ('>=', '<=', '!=', '==', '<', '>', '=', '<>')
        >>> for i in OPERATORS: check_threshold(1, i, 1)
        True
        True
        False
        True
        False
        False
        True
        False
    """
    if operator not in OPERATORS:
        raise InvalidThreshold('Invalid operator "%s", needs to be one of %s' % (operator, OPERATORS))
    elif operator == GE:
        return left >= right
    elif operator == LE:
        return left <= right
    elif operator == GT:
        return left > right
    elif operator == LT:
        return left < right
    elif operator in (EQ, EQ2):
        return left == right
    elif operator in (NE, NE2):
        return left != right
    else:
        raise NotSupported('Operator %s is not implemented yet.' % operator)