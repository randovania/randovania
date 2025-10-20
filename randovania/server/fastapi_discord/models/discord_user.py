from typing import Any

from pydantic import BaseModel


class DiscordUser(BaseModel):
    id: str
    username: str
    discriminator: int | None = None
    global_name: str | None = None
    avatar: str | None
    avatar_url: str | None = None
    locale: str
    email: str | None = None
    mfa_enabled: bool | None = None
    flags: int | None = None
    premium_type: int | None = None
    public_flags: int | None = None
    banner: str | None = None
    accent_color: int | None = None
    verified: bool | None = None
    avatar_decoration: str | None = None

    def __init__(self, **data: Any):
        super().__init__(**data)
        if self.avatar:
            self.avatar_url = f"https://cdn.discordapp.com/avatars/{self.id}/{self.avatar}.png"
        else:
            self.avatar_url = "https://cdn.discordapp.com/embed/avatars/1.png"
        if self.discriminator == 0:
            self.discriminator = None
