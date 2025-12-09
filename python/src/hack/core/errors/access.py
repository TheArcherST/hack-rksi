class ServiceAccessError(Exception):
    pass


class ErrorUnauthorized(ServiceAccessError):
    pass
