from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CategoriaCriar(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class CategoriaAtualizar(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)


class CategoriaLer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    created_at: datetime
