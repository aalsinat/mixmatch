from re import search

from zeep import Client
from datetime import datetime

from mixmatch.actions import IApplicable
from .exceptions import AuthenticationError

ACTION_NAME = 'IBERIA'


class RestClient(object):
    """
    A client needs REST API basic information, namely:
    - Credentials
    - Base URL
    - Operations URLs
    """

    def __new__(cls, iterable=(), **kwargs):
        if not hasattr(cls, 'instance') or not cls.instance:
            cls.instance = super(RestClient, cls).__new__(cls)
        return cls.instance

    def __init__(self, iterable=(), **kwargs):
        self.__dict__.update(iterable, **kwargs)
        self.__client = Client(self.base_url)
        self.__credentials = {'user': self.user, 'pwd': self.password}

    @staticmethod
    def __create_headers(content_type, accept, token):
        headers = {
            'Content-Type': content_type,
            'Accept': accept,
            'Authorization': 'Bearer {}'.format(token)
        }
        return headers

    def __get_token(self):
        try:
            login = self.__client.service.Login(**self.__credentials)
            if login.code == 'OK':
                return 200, login.tkn
        except Exception as e:
            raise AuthenticationError(str(e))

    def get_coupons(self, barcode):
        status, access_token = self.__get_token()
        headers = self.__create_headers('text/xml', 'text/xml', access_token)
        return status, access_token


class Action(IApplicable):
    def __init__(self, iterable=(), **properties):
        super(Action, self).__init__(iterable, **properties)

    def get_name(self):
        return ACTION_NAME

    def __get_client(self):
        return RestClient({
            'base_url': self['ws.base.url.test'],
            'user': self['ws.user'],
            'password': self['ws.pwd'],
            'airport': self['voucher.airport'],
            'id_provider': self['voucher.id_provider']
        })

    def __get_coupons(self, barcode):
        try:
            status, token = self.__get_client().get_coupons(barcode)
            self.logger.info('Login response: status: %d - token: %s', status, token)
        except AuthenticationError as e:
            self.logger.error(e)
            raise e

    def apply(self, icg_extend):
        # Check barcode to identify whether it is a ticket or a voucher
        is_voucher = True if search(r'^COUV', icg_extend.get_barcode()) is not None else False
        type = 'BON' if is_voucher else 'TKT'
        current_time = datetime.now()
        cs_date = current_time.strftime('%Y%m%d %H:%M')
        # We should call to GetVoucherAvailability service
        self.__get_coupons(icg_extend.get_barcode())
