from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.feature import Feature
from ..schemas.feature import FeatureCreate, FeatureUpdate
from .base import BaseRepository


class FeatureRepository(BaseRepository[Feature, FeatureCreate, FeatureUpdate]):
    def __init__(self):
        super().__init__(Feature)

    async def get_by_title(self, db: AsyncSession, title: str) -> Optional[Feature]:
        result = await db.execute(select(Feature).filter(Feature.title == title))
        return result.scalars().first()

    async def create_feature(
        self, db: AsyncSession, feature_schema: FeatureCreate
    ) -> Feature:
        existing_feature = await self.get_by_title(db, feature_schema.title)
        if existing_feature:
            raise ValueError(
                f"Feature с названием '{feature_schema.title}' уже существует"
            )

        return await self.create(db, feature_schema)

    async def update_feature(
        self,
        db: AsyncSession,
        feature_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Feature]:
        # Если новое название указано, проверяем уникальность
        if title:
            existing_feature = await self.get_by_title(db, title)
            if existing_feature and existing_feature.feature_id != feature_id:
                raise ValueError(f"Feature с названием '{title}' уже существует")

        feature_update = FeatureUpdate(title=title, description=description)
        return await self.update_by_id(db, feature_id, feature_update)


feature_repository = FeatureRepository()
