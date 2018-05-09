import asyncio
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

    def __init__(self, promotions, pos_api=None):
        self._actions = []
        # Loads all
        self.__load_actions(promotions['actions'].split(','))
        self.logger = getLogger(self.__class__.__module__)
        self.pos_api = pos_api

    def __load_actions(self, actions_list):
        for action in actions_list:
            action_module = import_module(''.join(['mixmatch.actions.', action.strip()]))
            self._actions.append(action_module.Action(settings[action.strip()]))

    async def __handle_request(self, reader, writer):
        data = await reader.read(8192)
        message = data.decode()
        addr = writer.get_extra_info('peername')
        self.logger.debug('Received %r from %r' % (message, addr))
        icg = ICGExtend(settings.icg.items())
        self.apply(self.pos_api)
        if len(message) > 1:
            self.logger.debug('Send: %r' % message)
            writer.write(data)
            await writer.drain()
            self.logger.debug('Close the client socket')
            writer.close()

    def serve(self):
        loop = asyncio.get_event_loop()
        coroutine = asyncio.start_server(self.__handle_request, '127.0.0.1', 8888, loop=loop)
        server = loop.run_until_complete(coroutine)

        # Serve requests until Ctrl+C is pressed
        print('Serving on {}'.format(server.sockets[0].getsockname()))
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass

        # Close the server
        server.close()
        loop.run_until_complete(server.wait_closed())
        loop.close()

    def apply(self, icg_extend):
        """
        This method searches in the list of loaded actions for the one corresponding to the pattern of the scanned
        value, and executes the apply method with the same value as the parameter.
        """
        icg_extend.reload_file()
        for action in self._actions:
            action.apply(icg_extend)


def setup_log():
    """ Sets up logging features, creating a log folder if it is neeeded """

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


def start():
    """
    This method is the entry point of the mix and match promotion.
    Applies the appropriate promotion depending on the contents
    of the ICG exchange file.
    """
    # Initialize logging features
    setup_log()
    promotion = Promotion(settings.promotions, ICGExtend(settings.icg.items()))
    # Start handling requests
    promotion.serve()


def apply(argv=None):
    """
    This method is the entry point of the mix and match promotion.
    Applies the appropriate promotion depending on the contents
    of the ICG exchange file.

    :param argv: Any list of parameters from the command line.

    """
    # Initialize log directory
    setup_log()
    Promotion(settings.promotions).apply(ICGExtend(settings.icg.items()))


__all__ = ['apply', 'start', 'Promotion']
