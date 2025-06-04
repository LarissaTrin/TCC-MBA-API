from pydantic import BaseModel


class CustomBaseModel(BaseModel):
    def dict(self, *args, **kwargs):
        d = self.model_dump(*args, **kwargs)
        d = {k: v for k, v in d.items() if v is not None}
        return d

    class Config:
        from_attributes = True
        orm_mode = True
