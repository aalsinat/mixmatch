from datetime import datetime
from logging import getLogger
from re import search

from lxml import etree
from requests import Session
from zeep import Client
from zeep import Plugin
from zeep.cache import SqliteCache
from zeep.transports import Transport

from mixmatch.actions import IApplicable
from .exceptions import AuthenticationError

ACTION_NAME = 'IBERIA'


class AddAuthorizationPlugin(Plugin):
    def __init__(self, logger):
        self.logger = logger
        self._token = None

    def egress(self, envelope, http_headers, operation, binding_options):
        try:
            if self._token is not None:
                http_headers.update(dict(Authorization=self._token))
            self.logger.info('Operation: %s - Http headers: %s', operation, str(http_headers))
            self.logger.info(etree.tostring(envelope, pretty_print=True))
        except etree.XMLSyntaxError:
            self.logger.error('Invalid XML content received.')
        return envelope, http_headers

    def set_token(self, token):
        self._token = token


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
        self.logger = getLogger(self.__module__)
        self._add_authorization = AddAuthorizationPlugin(self.logger)
        self._session = Session()
        self._session.verify = False
        self.__client = Client(self.base_url, plugins=[self._add_authorization],
                               transport=Transport(session=self._session, cache=SqliteCache()))
        self.__credentials = {'user': self.user, 'pwd': self.password}

    def __get_token(self):
        try:
            login = self.__client.service.Login(**self.__credentials)
            if login.code == 'OK':
                return 200, login.tkn
        except Exception as e:
            raise AuthenticationError(str(e))

    def get_coupons(self, barcode):
        status, access_token = self.__get_token()
        response = None
        if status == 200 and access_token is not None:
            self._add_authorization.set_token(access_token)
            # Check barcode to identify whether it is a ticket or a voucher
            is_voucher = True if search(r'^COUV', barcode) is not None else False
            type = 'BON' if is_voucher else 'TKT'
            current_time = datetime.now().strftime('%Y%m%d %H:%M')
            body = {
                'data': barcode,
                'type': type,
                'airport': self.airport,
                'idProvider': self.id_provider,
                'csdate': '20180402 12:00'  # current_time
            }
            response = self.__client.service.GetVoucherAvailability(**body)
        return status, response


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
        status, coupons = self.__get_client().get_coupons(barcode)
        self.logger.info('List of coupons:\n %s', coupons)

    def apply(self, icg_extend):
        """
        Si el codigo que escaneamos en un billete o un boarding pass, debemos mostrar la lista de vouchers
        que nos devuelve el servicio.
        En el caso de los bonos, la respuesta solo nos va a devolver una gratuidad, de modo que no debemos mostrar
        nada.
        :param icg_extend:
        :return:
        """
        # We should call to GetVoucherAvailability service
        try:
            self.__get_coupons(icg_extend.get_barcode())
        except AuthenticationError as auth:
            self.logger.error(auth.message)
        except Exception as e:
            self.logger.error(str(e))
