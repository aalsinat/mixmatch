from urllib3.exceptions import ConnectTimeoutError

from mixmatch.actions import IApplicable, PatternMatcher
from .api import RestClient
from .exceptions import InvalidQR

# Constants for returning status on view showing coupon list
VIEW_REDEEM = 'REDEEM'
VIEW_CANCEL = 'CANCEL'
VIEW_EXIT = 'EXIT'


class Action(IApplicable):
    ACTION_NAME = 'HYBRIS'
    promotion_pattern = r'^(AREAS-TIP:)(\d{2})(-COD:)(\d{9})(-.+)?$'

    def __init__(self, iterable=(), **properties):
        super(Action, self).__init__(iterable, **properties)
        self.promotions = self.__get_promotions(self['mixmatch.promotions'])

    def get_name(self):
        return type(self).ACTION_NAME

    @staticmethod
    def __get_promotions(raw_promotions):
        promos_list = raw_promotions.split('|')
        promos = {k: v for k, v in (promo.split(':') for promo in promos_list)}
        return promos

    @staticmethod
    def __get_user(barcode, matcher: PatternMatcher) -> str:
        return matcher.match(barcode, 4)[0]

    @staticmethod
    def __get_promotion_name(barcode: str, matcher: PatternMatcher) -> str:
        return matcher.match(barcode, 5)[0][1:]

    def check_pattern(self, barcode: str, matcher: PatternMatcher) -> tuple:
        return matcher.match(barcode, 4)

    def apply(self, icg_extend):
        matcher = PatternMatcher(self['mixmatch.pattern'])
        if self.check_pattern(icg_extend.get_barcode(), matcher) is None:
            self.logger.debug('Scanned value does not match %s patterns.', self.get_name())
            return

        self.logger.info('Applying %s action', self.get_name())
        try:
            coupons_list = self.__get_coupons(icg_extend.get_barcode())
            mix_and_match_status = '%s' % (','.join(map(lambda p: p['name'], coupons_list.pos)))
            icg_extend.set_mix_and_match_status(mix_and_match_status)
            self.activate_mix_match(icg_extend, coupons_list.promos)
            icg_extend.save_coupon(self.get_name(),
                                   dict(user_id=self.__get_user(icg_extend.get_barcode(), matcher),
                                        mm_code=coupons_list.promos,
                                        mm_name=self.__get_promotion_name(icg_extend.get_barcode(), matcher)))
        except InvalidQR as e:
            self.logger.error('An InvalidQR validation %d - %s', e.status, e.message)
            icg_extend.set_mix_and_match_status(e.message)
            icg_extend.cancel_mix_and_match()
        except ConnectTimeoutError as e:
            self.logger.error('Timeout connection error: %s', e.args[1])
            icg_extend.set_mix_and_match_status(e.args[1])
            icg_extend.cancel_mix_and_match()
        except Exception as e:
            self.logger.error('An exception has occurred %s', e)

    @staticmethod
    def activate_mix_match(icg_extend, promos):
        icg_extend.set_mix_and_match(promos[-1])
        icg_extend.activate_mix_and_match(promos)

    def __get_client(self):
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

    def __get_coupons(self, barcode):
        status, requested_coupons = self.__get_client().get_coupons(barcode)
        return requested_coupons
