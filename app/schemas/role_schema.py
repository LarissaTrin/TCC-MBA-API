from app.schemas.base import CustomBaseModel


class RoleSchemaBase(CustomBaseModel):
    id: int
    name: str
