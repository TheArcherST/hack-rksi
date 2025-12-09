from hack.rest_server.schemas.base import BaseDTO


class VerificationDTO(BaseDTO):
    code: int
