from uuid import uuid4

import pytest
from requests import Request, Session

from . import api_templates
from .base import PatchedRequest


class PatchedSession(Session):
    def prepsend(self, request: Request, **kwargs):
        kwargs.setdefault("verify", False)

        if isinstance(request, PatchedRequest):
            request.url = request.url.format(**request.path_params)

        return self.send(
            self.prepare_request(request),
            **kwargs,
        )


@pytest.fixture()
def client() -> PatchedSession:
    client = PatchedSession()
    return client
