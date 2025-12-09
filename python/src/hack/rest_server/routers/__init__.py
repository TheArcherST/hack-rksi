from fastapi import APIRouter

from . import (
    access,
    lead_sources,
    operators,
    lead_source_operators,
    appeals,
    inspect,
    debug,
)

router = APIRouter()


router.include_router(access.router)
router.include_router(lead_sources.router, include_in_schema=False)
router.include_router(operators.router, include_in_schema=False)
router.include_router(lead_source_operators.router, include_in_schema=False)
router.include_router(appeals.router, include_in_schema=False)
router.include_router(inspect.router, include_in_schema=False)
router.include_router(debug.router)


__all__ = [
    "router",
]
