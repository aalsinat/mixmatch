from importlib import import_module
from logging import getLogger, INFO, Formatter
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
        self._load_actions(promotions['actions'].split(','))
        self.logger = getLogger(self.__class__.__module__)

    def _load_actions(self, actions_list):
        for action in actions_list:
            action_module = import_module(''.join(['mixmatch.actions.', action]))
            self._actions.append(action_module.Action(settings[action]))

    def apply(self, icg_extend):
        """
        Esta metodo busca en la lista de acciones cargadas la que corresponda al identificador
        que se pasa como parametro y ejecuta el metodo apply con el valor de lo que se ha leido
        en el fichero de intercambio
        """
        for action in self._actions:
            if action.get_id() == icg_extend.get_promotion():
                self.logger.info('Applying action %s', action.get_name())
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
    directory = path.join(BASE_DIR, log_path)
    if not path.exists(directory):
        makedirs(directory)
    filename = path.join(directory, log_filename)
    logger = getLogger(__name__)
    logger.setLevel(INFO)
    formatter = Formatter(fmt='%(asctime)s - %(levelname)-8s - %(name)s %(message)s')
    # if not len(logger.handlers):
    handler = TimedRotatingFileHandler(filename, when='d', interval=1, backupCount=15)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info("Following promotions will be attempted: %s", settings.promotions['actions'])

    Promotion(settings.promotions).apply(ICGExtend(settings.icg.items()))


__all__ = ['apply', 'Promotion']
