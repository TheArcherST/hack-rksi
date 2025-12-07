from fastapi import APIRouter

from . import (
    access,
    lead_sources,
    operators,
    lead_source_operators,
    appeals,
    inspect,
)

router = APIRouter()


router.include_router(access.router)
router.include_router(lead_sources.router)
router.include_router(operators.router)
router.include_router(lead_source_operators.router)
router.include_router(appeals.router)
router.include_router(inspect.router)


__all__ = [
    "router",
]
