from fastapi import APIRouter

from . import (
    access,
    lead_sources,
    operators,
    lead_source_operators,
    appeals,
    inspect,
    debug,
    users,
    events,
)

router = APIRouter()


router.include_router(access.router, tags=["Access"])
router.include_router(users.router, tags=["Admin panel"])
router.include_router(events.router, tags=["Admin panel"])
router.include_router(debug.router, tags=["Debug"])

router.include_router(lead_sources.router, include_in_schema=False)
router.include_router(operators.router, include_in_schema=False)
router.include_router(lead_source_operators.router, include_in_schema=False)
router.include_router(appeals.router, include_in_schema=False)
router.include_router(inspect.router, include_in_schema=False)


__all__ = [
    "router",
]
