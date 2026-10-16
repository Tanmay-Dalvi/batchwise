"""API v1 router composition."""

from fastapi import APIRouter

from app.api.v1.batches import router as batches_router
from app.api.v1.calculate import router as calculate_router
from app.api.v1.health import router as health_router
from app.api.v1.parse import router as parse_router
from app.api.v1.recipes import router as recipes_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(health_router)
api_v1_router.include_router(calculate_router)
api_v1_router.include_router(parse_router)
api_v1_router.include_router(recipes_router)
api_v1_router.include_router(batches_router)

__all__ = ["api_v1_router"]

