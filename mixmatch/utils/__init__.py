from collections import namedtuple


def enum(**kwargs):
    """
    Creates an enum-like object by passing dictionary or keyword args
    """
    return namedtuple('Enum', kwargs.keys())(*kwargs.values())
