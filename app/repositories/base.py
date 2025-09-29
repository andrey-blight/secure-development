from abc import ABC
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseRepository(ABC, Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        pk_column = list(self.model.__table__.primary_key.columns)[0]
        result = await db.execute(select(self.model).filter(pk_column == id))
        return result.scalars().first()

    async def get_multi(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        result = await db.execute(select(self.model).offset(skip).limit(limit))
        return result.scalars().all()

    async def create(self, db: AsyncSession, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = obj_in.dict() if hasattr(obj_in, "dict") else obj_in
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        obj_data = (
            obj_in.dict(exclude_unset=True) if hasattr(obj_in, "dict") else obj_in
        )

        for field, value in obj_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update_by_id(
        self, db: AsyncSession, id: Any, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> Optional[ModelType]:
        db_obj = await self.get(db, id)
        if db_obj:
            return await self.update(db, db_obj, obj_in)
        return None

    async def remove(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        db_obj = await self.get(db, id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
            return db_obj
        return None

    async def remove_multi(self, db: AsyncSession, ids: List[Any]) -> int:
        pk_column = list(self.model.__table__.primary_key.columns)[0]
        result = await db.execute(delete(self.model).where(pk_column.in_(ids)))
        await db.commit()
        return result.rowcount

    async def count(self, db: AsyncSession) -> int:
        result = await db.execute(select(func.count()).select_from(self.model))
        return result.scalar()

    async def exists(self, db: AsyncSession, id: Any) -> bool:
        pk_column = list(self.model.__table__.primary_key.columns)[0]
        result = await db.execute(select(pk_column).filter(pk_column == id))
        return result.first() is not None
