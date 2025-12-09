from fastapi import APIRouter

from . import (
    access,
    users,
    events,
    events_cards,
    debug,
)

router = APIRouter()


router.include_router(access.router, tags=["Access"])
router.include_router(users.router, tags=["Admin panel"])
router.include_router(events_cards.router, tags=["Userspace"])
router.include_router(events.userspace_router, tags=["Userspace"])
router.include_router(events.admin_panel_router, tags=["Admin panel"])
router.include_router(debug.router, tags=["Debug"])


__all__ = [
    "router",
]
