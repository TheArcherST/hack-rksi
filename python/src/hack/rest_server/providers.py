from dishka import Provider, Scope, from_context, provide
from fastapi import FastAPI
from fastapi.requests import Request
from starlette.testclient import TestClient


class ProviderServer(Provider):
    app = from_context(FastAPI, scope=Scope.SESSION)
    request = from_context(provides=Request, scope=Scope.REQUEST)

    @provide(scope=Scope.SESSION, cache=False)
    def get_test_client(self, app: FastAPI) -> TestClient:
        return TestClient(app)
