"""Constants and convenience functions for host and service states.

Example usage:
    from pynag.Utils import states
    print states.OK, states.WARNING, states.CRITICAL, states.UNKNOWN

    print states.service_state_to_int('critical')
    print states.service_state_to_string(0)
    print states.host_state_to_int('UP')
    print states.host_state_to_string(1)
"""
import pynag.errors

OK, WARNING, CRITICAL, UNKNOWN = 0, 1, 2, 3
UP, DOWN, UNREACHABLE = 0, 1, 2

_SERVICE_TEXT_TO_INT = {
    'ok': OK,
    'warning': WARNING,
    'critical': CRITICAL,
    'unknown': UNKNOWN,

    # Common abbreviations:
    'warn': WARNING,
    'crit': CRITICAL,
    'w': WARNING,
    'c': CRITICAL,
    'u': UNKNOWN,

    # Numerical string representation of states:
    '0': OK,
    '1': WARNING,
    '2': CRITICAL,
    '3': UNKNOWN,
}

_HOST_TEXT_TO_INT = {
    'up': UP,
    'down': DOWN,
    'unreachable': UNREACHABLE,

    # Numerical string representation of states:
    '0': UP,
    '1': DOWN,
    '2': UNREACHABLE
}

_SERVICE_INT_TO_TEXT = {
    OK: 'OK',
    WARNING: 'Warning',
    CRITICAL: "Critical",
    UNKNOWN: 'Unknown'
}

_HOST_INT_TO_TEXT = {
    UP: 'Up',
    DOWN: 'Down',
    UNREACHABLE: 'Unreachable'
}


class UnknownState(pynag.errors.PynagError):
    """Raised when a state was inputed that we do not recognize."""


def service_state_to_int(state):
    """Converts from strings like OK to states like 0.

    Args:
        State: string. Can be in the form of 'ok', 'warning', 'critical', '1', etc.

    Returns:
        Integer. A nagios corresponding to the free text state inputted.

    Raises:
        UnknownState: If no match can be found for 'state'.

    Examples:
        >>> service_state_to_int('ok')
        0
        >>> service_state_to_int('Warning')
        1
        >>> service_state_to_int('critical')
        2
        >>> service_state_to_int('UNKNOWN')
        3
        >>> service_state_to_int('0')
        0
        >>> service_state_to_int('1')
        1
        >>> service_state_to_int('2')
        2
        >>> service_state_to_int('3')
        3
        >>> service_state_to_int('foo')
        Traceback (most recent call last):
          ..
        UnknownState: Do not know how to handle state foo

    """
    text = str(state).lower()
    try:
        return _SERVICE_TEXT_TO_INT[text]
    except KeyError:
        raise UnknownState('Do not know how to handle state %s' % state)


def service_state_to_string(state):
    """Converts from integer or text to a formal text representation of a nagios state.

    Args:
        State: integer or string. e.g. 0,1,2,3 or 'warn', 'crit'

    Returns:
        String. Formal description of a specified nagios state.

    Raises:
        UnknownState: If no match can be found for 'state'.

    Examples:
        >>> service_state_to_string(0)
        'OK'
        >>> service_state_to_string(1)
        'Warning'
        >>> service_state_to_string(2)
        'Critical'
        >>> service_state_to_string(3)
        'Unknown'
        >>> service_state_to_string('ok')
        'OK'
        >>> service_state_to_string('warn')
        'Warning'
        >>> service_state_to_string('foo')
        Traceback (most recent call last):
          ..
        UnknownState: Do not know how to handle state foo

    """
    integer = service_state_to_int(state)
    return _SERVICE_INT_TO_TEXT[integer]


def host_state_to_int(state):
    """Converts from strings like UP to states like 0.

    Args:
        State: string. Can be in the form of 'UP', 'Down', 'Unreachable', '1', etc.

    Returns:
        String. Formal description of a specified nagios state.

    Raises:
        UnknownState: If no match can be found for 'state'.

    Examples:
        >>> host_state_to_int('up')
        0
        >>> host_state_to_int('Down')
        1
        >>> host_state_to_int('UNREACHABLE')
        2
        >>> host_state_to_int(0)
        0
        >>> host_state_to_int(3)
        Traceback (most recent call last):
         ..
        UnknownState: Do not know how to handle state 3

    """
    text = str(state).lower()
    try:
        return _HOST_TEXT_TO_INT[text]
    except KeyError:
        raise UnknownState('Do not know how to handle state %s' % state)


def host_state_to_string(state):
    """Converts from integer or text to a formal text representation of a nagios state.

    Args:
        State: string. Can be in the form of 'ok', 'warning', 'critical', '1', etc.

    Returns:
        Integer. A nagios corresponding to the free text state inputted.

    Raises:
        UnknownState: If no match can be found for 'state'.

    Examples:
        >>> host_state_to_string(0)
        'Up'
        >>> host_state_to_string(1)
        'Down'
        >>> host_state_to_string(2)
        'Unreachable'
        >>> host_state_to_string('DOWN')
        'Down'
    """
    integer = host_state_to_int(state)
    return _HOST_INT_TO_TEXT[integer]
