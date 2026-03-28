
from iceaxe import Field, TableBase


class DetailItem(TableBase):
    id: int | None = Field(default=None, primary_key=True)
    description: str
