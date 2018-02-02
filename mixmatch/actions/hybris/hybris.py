from urllib3.exceptions import ConnectTimeoutError

from mixmatch.actions import IApplicable
from .api import RestClient
from .exceptions import InvalidQR

# Constants for returning status on view showing coupon list
VIEW_REDEEM = 'REDEEM'
VIEW_CANCEL = 'CANCEL'
VIEW_EXIT = 'EXIT'
ACTION_NAME = 'HYBRIS'


class Action(IApplicable):
    def __init__(self, iterable=(), **properties):
        super(Action, self).__init__(iterable, **properties)

    def get_name(self):
        return ACTION_NAME

    def apply(self, icg_extend):
        self.logger.info('Showing coupons list')
        try:
            coupons_list = self._get_coupons(icg_extend.get_barcode())
            # UPDATE mixmatch.xmlFile
            mix_and_match_status = '%s: %s' % (
            self['mixmatch.message'], ','.join(map(lambda p: p['code'], coupons_list.pos)))
            mix_and_match_code = coupons_list.promos[-1]
            icg_extend.set_mix_and_match_status(mix_and_match_status)
            icg_extend.set_mix_and_match_value(mix_and_match_code)
        except InvalidQR as e:
            self.logger.error('An InvalidQR validation %d - %s', e.status, e.message)
            icg_extend.set_mix_and_match_status(e.message)
            icg_extend.set_mix_and_match_value('0')
        except ConnectTimeoutError as e:
            self.logger.error('Timeout connection error: %s', e.args[1])
            icg_extend.set_mix_and_match_status(e.args[1])
            icg_extend.set_mix_and_match_value('0')
        except Exception as e:
            self.logger.error('An exception has occurred %s', e.message)

    def _get_client(self):
        return RestClient({
            'grant_type': self['token.grant_type'],
            'client_id': self['token.client_id'],
            'client_secret': self['token.client_secret'],
            'username': self['token.username'],
            'password': self['token.password'],
            'base_url': self['ws.base.url'],
            'login_url': self['ws.token.url'],
            'coupons_url': self['ws.base.url.validateqr'],
            'codTPV': self['tvp.codtpv']
        })

    def _get_coupons(self, barcode):
        status, requested_coupons = self._get_client().get_coupons(barcode)
        return requested_coupons
