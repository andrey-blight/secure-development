from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ....db import get_session
from ....repositories import feature_repository

router = APIRouter(prefix="/feature", tags=["feature"])


@router.get("/")
async def get_features(
    db: AsyncSession = Depends(get_session), skip: int = 0, limit: int = 100
):
    features = await feature_repository.get_multi(db, skip, limit)
    return features
