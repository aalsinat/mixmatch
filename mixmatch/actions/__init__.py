from logging import getLogger
from re import compile


class PatternMatcher(object):
    def __init__(self, pattern: str):
        self.__matcher = compile(pattern)

    def match(self, string: str, *return_values) -> tuple:
        """
        Given a regular expression pattern, returns the values or list of values of the indicated groups.
        :rtype: object
        :param string: Value to be scanned
        :param return_values: List of groups to be returned.
        :return: tuple containing all requested groups
        """
        values = []
        result = self.__matcher.match(string)
        if result is not None:
            for value in return_values:
                values.append(result.group(int(value)))
            return tuple(values)
        else:
            return result


class IApplicable(object):
    def __init__(self, iterable=(), **properties):
        self.logger = getLogger(self.__module__)
        self.__dict__.update(iterable, **properties)

    def get_id(self):
        return int(self['mixmatch.id'])

    def get_name(self):
        raise Exception('Method not implemented!')

    def check_pattern(self, barcode: str, matcher: PatternMatcher):
        """
        Check that the scanned value matches any of the patterns accepted by the action.
        :param barcode: Scanned value
        :param matcher: Pattern matcher to be used
        :return: None if scanned value does not match any pattern. Otherwise it returns a value useful for the
        application of the action.
        """
        raise Exception('Method not implemented!')

    def apply(self, icg_extend):
        """
        Applies the action corresponding to the selected promotion.
        :param icg_extend: Point of sales software interface
        :return: If any coupon has been selected by UI, it will be stored on an exchange file.
        """
        raise Exception('Method not implemented!')

    def __getattr__(self, name):
        return getattr(self, name)

    __getitem__ = __getattr__
