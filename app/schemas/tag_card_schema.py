from typing import Optional

from app.schemas.base import CustomBaseModel
from app.schemas.tag_schema import TagSchemaBase


class TagCardSchemaBase(CustomBaseModel):
    id: Optional[int] = None
    tag_id: Optional[int] = None


class TagCardSchema(TagCardSchemaBase):
    tag: Optional[TagSchemaBase] = None
