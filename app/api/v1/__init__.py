from fastapi import APIRouter

from .endpoints import feature_router

router = APIRouter(prefix="/v1")
router.include_router(feature_router)
