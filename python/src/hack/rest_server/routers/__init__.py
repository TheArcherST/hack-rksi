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


router.include_router(access.router)
router.include_router(lead_sources.router, include_in_schema=False)
router.include_router(operators.router, include_in_schema=False)
router.include_router(lead_source_operators.router, include_in_schema=False)
router.include_router(appeals.router, include_in_schema=False)
router.include_router(inspect.router, include_in_schema=False)
router.include_router(debug.router)
router.include_router(users.router)
router.include_router(events.router)


__all__ = [
    "router",
]
