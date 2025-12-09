class ServiceAccessError(Exception):
    pass


class ErrorUnauthorized(ServiceAccessError):
    pass


class ErrorVerification(ServiceAccessError):
    pass


class ErrorEmailAlreadyExists(ServiceAccessError):
    pass
