from fastapi import APIRouter

from . import (
    lead_sources,
    operators,
    lead_source_operators,
    appeals,
)

router = APIRouter()


router.include_router(lead_sources.router)
router.include_router(operators.router)
router.include_router(lead_source_operators.router)
router.include_router(appeals.router)


__all__ = [
    "router",
]
