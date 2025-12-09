from fastapi import APIRouter

from . import (
    access,
    debug,
    users,
    events,
)

router = APIRouter()


router.include_router(access.router, tags=["Access"])
router.include_router(users.router, tags=["Admin panel"])
router.include_router(events.router, tags=["Admin panel"])
router.include_router(debug.router, tags=["Debug"])


__all__ = [
    "router",
]
