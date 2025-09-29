from typing import Optional

from pydantic import BaseModel, ConfigDict


class FeatureBase(BaseModel):
    title: str
    description: str


class FeatureCreate(FeatureBase):
    pass


class FeatureUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class Feature(FeatureBase):
    feature_id: int

    model_config = ConfigDict(from_attributes=True)
