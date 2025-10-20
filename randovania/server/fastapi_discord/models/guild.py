from pydantic import BaseModel

from .role import Role


class GuildPreview(BaseModel):
    id: str
    name: str
    icon: str | None = None
    owner: bool
    permissions: int
    features: list[str]


class Guild(GuildPreview):
    owner_id: int | None = None
    verification_level: int | None = None
    default_message_notifications: int | None = None
    roles: list[Role] | None = None
