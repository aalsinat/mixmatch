from json import loads, dumps

from urllib3 import PoolManager


class Coupon(object):

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


class RestClient(object):
    """
    A client needs REST API basic information, namely
    - Credentials
    - Base url
    - Operation urls
    """

    def __init__(self, iterable=(), **kwargs):
        self.http_client = PoolManager()
        self.__dict__.update(iterable, **kwargs)

    def __getitem__(self, item):
        return getattr(self, item)

    @staticmethod
    def _create_headers(content_type, token):
        headers = {
            'Content-Type': content_type,
            'Accept': content_type,
            'Authorization': 'Bearer {}'.format(token)
        }
        return headers

    def _get_token(self):
        body = {
            'grant_type': self.grant_type,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        token_response = self.http_client.request_encode_body(method='POST',
                                                              url=''.join([self.base_url,
                                                                           self.login_url]),
                                                              fields=body,
                                                              encode_multipart=False, timeout=3, retries=False)
        if token_response.status == 200:
            return token_response.status, loads(token_response.data.decode('utf-8'))['access_token']
        else:
            return token_response.status, loads(token_response.data.decode('utf-8'))['error']

    def get_coupons(self, barcode):
        status, access_token = self._get_token()
        if status == 200:
            headers = self._create_headers('application/json', access_token)
            data = {
                'barcode': barcode,
                'barcodeFormat': 'auto',
                'locationRef': self.location,
                'serviceProviderRef': self.service_provider,
                'tradingOutletRef': self.trading_outlet
            }
            encoded_data = dumps(data).encode('utf-8')
            coupons_list = self.http_client.request('POST', ''.join(
                [self.base_url, self.coupons_url]), body=encoded_data,
                                                    headers=headers, timeout=3, retries=False)
            if coupons_list.status == 200:
                coupons = map(lambda c: Coupon(c), loads(coupons_list.data.decode('utf-8'))['coupons'])
                return coupons_list.status, coupons
            else:
                return coupons_list.status, loads(coupons_list.data.decode('utf-8'))['message']
        else:
            raise Exception('Authentication error %s: %s' % (status, access_token))
