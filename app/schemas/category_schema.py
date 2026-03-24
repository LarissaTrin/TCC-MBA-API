from app.schemas.base import CustomBaseModel


class CategorySchema(CustomBaseModel):
    """Serialization schema for a card category."""

    id: int
    name: str
