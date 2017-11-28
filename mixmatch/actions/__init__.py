import logging

__all__ = ['Action']


class Action(object):
    def __init__(self, constructor=()):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.values = list(constructor)
        self.properties = dict(self.values)

    @classmethod
    def from_values(cls, *args):
        return cls(args)

    def __iter__(self):
        return iter(self.values)

    @classmethod
    def from_list(cls, properties_list):
        return cls(properties_list)
