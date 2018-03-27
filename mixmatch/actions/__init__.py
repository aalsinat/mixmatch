from logging import getLogger


class IApplicable(object):
    def __init__(self, iterable=(), **properties):
        self.logger = getLogger(self.__module__)
        self.__dict__.update(iterable, **properties)

    def get_id(self):
        return int(self['mixmatch.id'])

    def get_name(self):
        raise Exception('Method not implemented!')

    def apply(self, icg_extend):
        raise Exception('Method not implemented!')

    def __getattr__(self, name):
        return getattr(self, name)

    __getitem__ = __getattr__
