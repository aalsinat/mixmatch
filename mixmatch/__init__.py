from importlib import import_module
from logging import getLogger, Formatter, INFO, DEBUG
from logging.handlers import TimedRotatingFileHandler
from os import path, makedirs

from mixmatch.conf import settings, BASE_DIR
from mixmatch.core.icg import ICGExtend


class Promotion(object):
    """
    This class is the entry point for the application of promotions and discounts. It will be responsible for uploading
    all available and selected actions. Based on the ICG transfer file he decides which action should be executed.
    """

    def __init__(self, promotions):
        self._actions = []
        # Loads all
        self._load_actions(promotions['actions'].split(','))
        self.logger = getLogger(self.__class__.__module__)

    def _load_actions(self, actions_list):
        for action in actions_list:
            action_module = import_module(''.join(['mixmatch.actions.', action.strip()]))
            self._actions.append(action_module.Action(settings[action.strip()]))

    def apply(self, icg_extend):
        """
        This method searches in the list of loaded actions for the one corresponding to the pattern of the scanned
        value, and executes the apply method with the same value as the parameter.
        """
        for action in self._actions:
            action.apply(icg_extend)

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
    log_debug = eval(settings.log['debug'])
    directory = path.join(BASE_DIR, log_path)
    if not path.exists(directory):
        makedirs(directory)
    filename = path.join(directory, log_filename)
    logger = getLogger(__name__)
    if log_debug:
        logger.setLevel(DEBUG)
    else:
        logger.setLevel(INFO)
    formatter = Formatter(fmt='%(asctime)s - %(levelname)-8s - %(name)s %(message)s')
    # if not len(logger.handlers):
    handler = TimedRotatingFileHandler(filename, when='d', interval=1, backupCount=15)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info("Following promotions will be attempted: %s", settings.promotions['actions'])

    Promotion(settings.promotions).apply(ICGExtend(settings.icg.items()))


__all__ = ['apply', 'Promotion']

