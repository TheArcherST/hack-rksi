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


class ErrorRegistrationRateLimited(ServiceAccessError):
    def __init__(self, retry_after: int):
        super().__init__("Registration verification rate limit exceeded")
        self.retry_after = retry_after
