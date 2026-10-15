from typing import Annotated

import pydantic


class GuildPreferences(pydantic.BaseModel):
    multiworld_interest_role_id: int | None = None

    multiworld_interest_ping_cooldown: Annotated[int, "seconds"] = pydantic.Field(default=120)
