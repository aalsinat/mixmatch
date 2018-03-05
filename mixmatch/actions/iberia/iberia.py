from logging import getLogger

from zeep import Client

from mixmatch.actions import IApplicable

ACTION_NAME = 'iberia'


class Action(IApplicable):
    def __init__(self, iterable=(), **properties):
        super(Action, self).__init__(iterable, **properties)
        self.logger = getLogger(self.__class__.__name__)

    def get_name(self):
        return ACTION_NAME

    def apply(self, identifier, icg_extend):
        self.logger.info('By now doing nothing')
        pass

    def get_token(self):
        client = Client(self['ws.base.url.test'])
        credentials = {'user': self['ws.user'],
                       'pwd': self['ws.pwd']}
        return client.service.Login(credentials)
