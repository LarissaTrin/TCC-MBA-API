from typing import Optional

from app.schemas.base import CustomBaseModel


class TagSchemaBase(CustomBaseModel):
    id: Optional[int] = None
    name: Optional[int] = None
