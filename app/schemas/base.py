from pydantic import BaseModel
from pydantic.alias_generators import to_camel


class CustomBaseModel(BaseModel):
    def dict(self, *args, **kwargs):
        d = self.model_dump(*args, **kwargs)
        d = {k: v for k, v in d.items() if v is not None}
        return d

    class Config:
        from_attributes = True
        populate_by_name = True
        alias_generator = to_camel
