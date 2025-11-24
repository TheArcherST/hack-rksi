import uvicorn
from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hack.core.providers import ProviderConfig, ProviderDatabase
from hack.core.services.providers import ProviderServices
from hack.rest_server import (
    exception_handlers,
    routers,
)
from hack.rest_server.providers import ProviderServer


def main():
    providers = (
        ProviderConfig(),
        ProviderDatabase(),
        ProviderServices(),
        ProviderServer(),
    )
    container = make_async_container(*providers)

    app = FastAPI()
    setup_dishka(container, app)

    exception_handlers.register(app)
    app.include_router(routers.router)

    app.add_middleware(  # todo: adjust [sec]
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_event_handler("shutdown", container.close)

    uvicorn.run(app, host="0.0.0.0", port=80)


if __name__ == "__main__":
    main()
