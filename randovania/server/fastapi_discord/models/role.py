from pydantic import BaseModel


class Role(BaseModel):
    id: int
    name: str
    color: int
    position: int
    permissions: int
    managed: bool
    mentionable: bool
