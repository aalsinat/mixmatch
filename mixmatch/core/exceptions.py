class ImproperlyConfigured(Exception):
    """Reader is somehow improperly configured"""
    pass


class DatabaseConnectionException(Exception):
    """
    Connection to ICG Local database was not successful
    """
    def __init__(self, message: str) -> None:
        self.message = message
