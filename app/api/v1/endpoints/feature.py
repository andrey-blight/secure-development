from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ....db import get_session
from ....repositories import feature_repository
from ....schemas.feature import Feature, FeatureCreate, FeatureUpdate

router = APIRouter(prefix="/feature", tags=["feature"])


@router.get("/search", response_model=List[Feature])
async def search_feature_by_title(
    title: str,
    db: AsyncSession = Depends(get_session),
):
    feature = await feature_repository.find_by_title(db, title)
    if not feature:
        raise HTTPException(
            status_code=404, detail=f"Feature with title '{title}' not found"
        )
    return feature


@router.get("/", response_model=List[Feature])
async def get_features(
    db: AsyncSession = Depends(get_session), skip: int = 0, limit: int = 100
):
    features = await feature_repository.get_multi(db, skip, limit)
    return features


@router.get("/{feature_id}", response_model=Feature)
async def get_feature(
    feature_id: int,
    db: AsyncSession = Depends(get_session),
):
    feature = await feature_repository.get(db, feature_id)
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    return feature


@router.post("/", response_model=Feature)
async def create_feature(
    db: AsyncSession = Depends(get_session),
    feature: FeatureCreate = Body(...),
):
    try:
        feature = await feature_repository.create_feature(db, feature)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return feature


@router.put("/{feature_id}", response_model=Feature)
async def update_feature(
    feature_id: int,
    db: AsyncSession = Depends(get_session),
    feature: FeatureUpdate = Body(...),
):
    try:
        updated_feature = await feature_repository.update_feature(
            db, feature_id, feature
        )
        if not updated_feature:
            raise HTTPException(status_code=404, detail="Feature not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return updated_feature


@router.delete("/{feature_id}", response_model=Feature)
async def delete_feature(
    feature_id: int,
    db: AsyncSession = Depends(get_session),
):
    feature = await feature_repository.remove(db, feature_id)
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    return feature
