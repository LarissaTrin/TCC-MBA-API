from typing import Optional

from app.schemas.base import CustomBaseModel
from app.schemas.card_schema import CardSchema


class ListSchemaBase(CustomBaseModel):
    name: str
    order: int
    is_final: bool = False


class ListSchemaUp(CustomBaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    order: Optional[int] = None
    is_final: Optional[bool] = None


class ListSchema(ListSchemaBase):
    id: int

    cards: Optional[list[CardSchema]] = []


class ListSchemaProject(ListSchemaBase):
    id: int
    project_id: int
