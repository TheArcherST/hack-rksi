class ServiceAccessError(Exception):
    pass


class ErrorUnauthorized(ServiceAccessError):
    pass


class ErrorVerification(ServiceAccessError):
    pass


class ErrorEmailAlreadyExists(ServiceAccessError):
    pass


class ErrorRecovery(ServiceAccessError):
    pass


class ErrorRecoveryEmailNotFound(ErrorRecovery):
    pass


class ErrorRecoveryTokenInvalid(ErrorRecovery):
    pass


class ErrorRecoveryTokenExpired(ErrorRecovery):
    pass
