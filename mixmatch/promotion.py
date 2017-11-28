import logging
import os

from mixmatch.actions.icoupon import ICoupon
from mixmatch.conf import settings, BASE_DIR
from mixmatch.core.icg import ICGExtend


def apply(argv=None):
    """
    This method is the entry point of the mix and match promotion.
    Applies the appropriate promotion depending on the contents
    of the ICG exchange file.

    :param argv: Any list of parameters from the command line.

    """
    # Initialize log directory
    log_path = settings.log['path']
    log_filename = settings.log['name']
    directory = os.path.join(BASE_DIR, log_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    filename = os.path.join(directory, log_filename)

    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s', filename=filename)
    logger = logging.getLogger(__name__)
    logger.info("Current application path: %s", BASE_DIR)

    icg_extend = ICGExtend(settings.icg.items())
    if icg_extend.get_promotion() == int(settings.icoupon['mixmatch.id']):
        promotion = ICoupon(settings.icoupon.items()).show_coupons(icg_extend.get_barcode(), icg_extend)
