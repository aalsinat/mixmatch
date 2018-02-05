import importlib
import importlib.util
import logging

import os

from mixmatch.conf import settings, BASE_DIR
from mixmatch.core.icg import ICGExtend


class Promotion(object):
    """
    Esta clase es el punto de entrada para la aplicacion de promociones y descuentos.
    Sera la responsable de cargar todas las acciones disponibles y seleccionadas.
    En base al fichero de intercambio de ICG decide que accion debe ejecutarse
    """

    def __init__(self, promotions):
        self._actions = []
        self._load_actions(promotions['actions'].split(','))
        self.logger = logging.getLogger(self.__class__.__name__)

    def _load_actions(self, actions_list):
        for action in actions_list:
            action_module = importlib.import_module(''.join(['mixmatch.actions.', action]))
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
    directory = os.path.join(BASE_DIR, log_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    filename = os.path.join(directory, log_filename)

    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s', filename=filename)
    logger = logging.getLogger(__name__)
    logger.info("Current application path: %s", BASE_DIR)

    Promotion(settings.promotions).apply(ICGExtend(settings.icg.items()))
