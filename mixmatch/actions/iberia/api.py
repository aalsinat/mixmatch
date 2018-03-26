from datetime import datetime
from logging import getLogger
from re import search, split
from json import loads, dumps

from lxml import etree
from requests import Session
from zeep import Client
from zeep import Plugin
from zeep.cache import InMemoryCache
from zeep.transports import Transport

from .exceptions import VoucherAvailabilityRequestError, AuthenticationError


class ProvidedCoupon(object):
    def __init__(self, iterable=(), **kwargs):
        self.selected = False
        self.__dict__.update(iterable, **kwargs)

    def __repr__(self):
        return dumps(self.__dict__, sort_keys=False, indent=2, separators=(',', ': '))

    def __getitem__(self, item):
        return getattr(self, item)

    def __hash__(self):
        return hash(self.couponRef)

    def __eq__(self, other):
        return self.couponRef == other.couponRef

    def __str__(self):
        return self.__repr__()


class Coupon(object):
    def __init__(self, identifier, name, is_redeemable):
        self.selected = False
        self.id = identifier
        self.name = name
        self.is_redeemable = is_redeemable

    def __repr__(self):
        return dumps(self.__dict__, sort_keys=False, indent=2, separators=(',', ': '))

    def __str__(self):
        return self.__repr__()

    @classmethod
    def from_provided(cls, translation, provided_coupon, is_redeemable):
        return cls(identifier=provided_coupon[translation['id']],
                   name=provided_coupon[translation['name']],
                   is_redeemable=is_redeemable)


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
        self._add_authorization = self.AuthorizationPlugin(self.logger)
        self._session = Session()
        self._session.verify = False
        self.__client = Client(self.base_url, plugins=[self._add_authorization],
                               transport=Transport(session=self._session, cache=InMemoryCache()))
        self.__credentials = {'user': self.user, 'pwd': self.password}

    def __get_token(self):
        try:
            login = self.__client.service.Login(**self.__credentials)
            if login.code == 'OK':
                return 200, login.tkn
            else:
                raise AuthenticationError('Authentication error code: {}'.format(login.code))
        except Exception as e:
            raise AuthenticationError(str(e))

    @staticmethod
    def __is_voucher(barcode):
        return True if search(r'^0002\d{2}', barcode) is not None else False

    @staticmethod
    def __get_voucher_id(barcode):
        return split(r'^0002\d{2}', barcode)[1]

    def __check_type(self, barcode):
        """ Given a barcode tries to find out what type of document has been scanned"""
        return {'data': self.__get_voucher_id(barcode), 'type': 'BON'} if self.__is_voucher(barcode) else {
            'data': barcode, 'type': 'TKT'}

    def is_voucher(self, scanned_string):
        return self.__is_voucher(scanned_string)

    @staticmethod
    def __to_coupons(translation, provided_list):
        coupons = map(lambda cp: Coupon.from_provided(translation, cp, cp.status == 'ABIERTO' and cp.outdate is None),
                      provided_list)
        return list(coupons)

    def get_coupons(self, barcode):
        status, access_token = self.__get_token()
        self._add_authorization.set_token(access_token)
        body = self.__check_type(barcode)
        body.update({
            'airport': self.airport,
            'idProvider': self.id_provider,
            'csdate': '20180322 12:00'  # datetime.now().strftime('%Y%m%d %H:%M')
        })
        response = self.__client.service.GetVoucherAvailability(**body)
        if response.code == 'OK':
            return status, self.__to_coupons({'id': 'id', 'name': 'nbre_svc'}, response.vouchers.voucher)
        else:
            raise VoucherAvailabilityRequestError(
                'Response code from GetVoucherAvailability is {}'.format(response.code))

    class AuthorizationPlugin(Plugin):
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
