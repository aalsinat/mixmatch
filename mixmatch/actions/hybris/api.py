import json

import urllib3

from .exceptions import InvalidQR


class Coupon(object):
    def __init__(self, iterable=(), **kwargs):
        self.selected = False
        self.__dict__.update(iterable, **kwargs)

    def __repr__(self):
        return json.dumps(self.__dict__, sort_keys=False, indent=2, separators=(',', ': '))

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
        self.http_client = urllib3.PoolManager()
        self.__dict__.update(iterable, **kwargs)

    def __getitem__(self, item):
        return getattr(self, item)

    @staticmethod
    def _create_headers(content_type, token, accept=None):
        headers = {
            'Content-Type': content_type,
            'Accept': accept if accept is not None else content_type,
            'Authorization': 'Bearer {}'.format(token)
        }
        return headers

    def _get_token(self):
        body = {
            'grant_type': self.grant_type,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'username': self.username,
            'password': self.password
        }
        token_response = self.http_client.request_encode_body(method='POST',
                                                              url=''.join([self.base_url,
                                                                           self.login_url]),
                                                              fields=body,
                                                              encode_multipart=False, timeout=3, retries=False)
        if token_response.status == 200:
            return token_response.status, json.loads(token_response.data.decode('utf-8'))['access_token']
        else:
            return token_response.status, json.loads(token_response.data.decode('utf-8'))['error']

    def get_coupons(self, barcode):
        status, access_token = self._get_token()
        if 200 <= status < 300:
            headers = self._create_headers('application/x-www-form-urlencoded', access_token, 'application/json')
            data = {
                'qrCode': barcode,
                'codTPV': self.codTPV
            }
            #            encoded_data = json.dumps(data).encode('utf-8')
            encoded_data = data
            coupons_list = self.http_client.request_encode_body(method='POST',
                                                                url=''.join([self.base_url,
                                                                             self.coupons_url]),
                                                                fields=encoded_data,
                                                                headers=headers,
                                                                encode_multipart=False, timeout=3, retries=False)

            if 200 <= coupons_list.status < 300:
                coupons = Coupon(
                    json.loads(json.loads(coupons_list.data.decode('utf-8'))["message"].replace("'", "\"")))
                return coupons_list.status, coupons
            else:
                raise InvalidQR(coupons_list.status, json.loads(coupons_list.data.decode('utf-8'))['message'])
        #                return coupons_list.status, json.loads(coupons_list.data.decode('utf-8'))['message']
        else:
            raise Exception('Authentication error %s: %s' % (status, access_token))
