from zeep import Client


class IberiaRequest(object):
    def __init__(self, constructor=()):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.values = list(constructor)
        self.properties = dict(self.values)

    @classmethod
    def from_values(cls, *args):
        return cls(args)

    @classmethod
    def from_list(cls, properties_list):
        return cls(properties_list)

    def get_token(self):
        client = Client(self.properties.get('ws.base.url.test'))
        credentials = {'user': self.properties.get('ws.user'),
                       'pwd': self.properties.get('ws.pwd')}
        return client.service.Login(credentials)