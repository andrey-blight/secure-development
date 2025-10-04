from typing import Optional

from pydantic import BaseModel, ConfigDict, constr


class FeatureBase(BaseModel):
    title: constr(min_length=1)
    description: constr(min_length=1)


class FeatureCreate(FeatureBase):
    pass


class FeatureUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class Feature(FeatureBase):
    feature_id: int

    model_config = ConfigDict(from_attributes=True)
