from typing import Optional

from app.schemas.base import CustomBaseModel
from app.schemas.user_schema import UserSchemaBase


class ApproverSchemaBase(CustomBaseModel):
    id: Optional[int] = None
    environment: Optional[str] = None
    user_id: Optional[int] = None


class ApproverSchema(ApproverSchemaBase):
    user: Optional[UserSchemaBase] = None
