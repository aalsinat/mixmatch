class AuthenticationError(Exception):
    def __init__(self, message):
        self.message = message


class VoucherAvailabilityRequestError(Exception):
    def __init__(self, message):
        self.message = message
