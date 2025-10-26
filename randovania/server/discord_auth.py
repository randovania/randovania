from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Self, TypedDict

import aiohttp

from randovania.lib import http_lib
from randovania.server.fastapi_discord import DiscordOAuthClient

if TYPE_CHECKING:
    from randovania.server.server_app import Lifespan, RdvFastAPI, ServerApp


class EnforceRoleConfiguration(TypedDict, total=True):
    guild_id: int
    role_id: int | str
    token: str


class EnforceDiscordRole:
    guild_id: int
    role_id: str
    sa: ServerApp
    session: aiohttp.ClientSession

    @classmethod
    @asynccontextmanager
    async def lifespan(cls, _app: RdvFastAPI) -> Lifespan[Self | None]:
        config = _app.sa.configuration["server_config"].get("enforce_role")
        if config is None:
            yield None
            return

        self = cls()
        self.sa = _app.sa
        self.guild_id = config["guild_id"]
        self.role_id = str(config["role_id"])
        async with http_lib.http_session() as self.session:
            self.session.headers["Authorization"] = "Bot {}".format(config["token"])
            yield self

    async def verify_user(self, user_id: str) -> bool:
        url = f"https://discordapp.com/api/guilds/{self.guild_id}/members/{user_id}"
        async with self.session.get(url) as r:
            try:
                if r.ok:
                    result = await r.json()
                    return self.role_id in result["roles"]
                else:
                    self.sa.logger.warning("Unable to verify user %s: %s", user_id, await r.text())
                    return False

            except aiohttp.ClientError as e:
                self.sa.logger.warning("Unable to verify user %s: %s / %s", user_id, await r.text(), str(e))
                return True


@asynccontextmanager
async def discord_oauth_lifespan(_app: RdvFastAPI) -> Lifespan[DiscordOAuthClient]:
    config = _app.sa.configuration

    client_id = config["discord_client_id"]
    client_secret = config["server_config"]["discord_client_secret"]
    redirect_uri = ""  # let the server route the redirect

    scopes = ("identify",)

    discord = DiscordOAuthClient(str(client_id), client_secret, redirect_uri, scopes)

    await discord.init()

    yield discord

    if discord.client_session is not None:
        await discord.client_session.close()
        discord.client_session = None
