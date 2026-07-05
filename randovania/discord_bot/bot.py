import hashlib
import logging
from typing import Required, TypedDict

import aiohttp
import discord

import randovania
from randovania.discord_bot.randovania_cog import RandovaniaCog
from randovania.lib import http_lib
from randovania.network_common import connection_headers
from randovania.network_common.configuration import NetworkConfiguration


async def application_command_error(ctx: discord.ApplicationContext, error: discord.DiscordException):
    logging.exception(
        "Exception when user %s used %s with args %s",
        str(ctx.user),
        ctx.command.qualified_name,
        str(ctx.selected_options),
        exc_info=error,
    )
    await ctx.respond("Sorry, an error has occurred processing the request.", ephemeral=True)


class BotConfiguration(TypedDict, total=False):
    token: Required[str]
    debug_guild: int
    command_prefix: str


class RandovaniaBot(discord.Bot):
    rdv_http: aiohttp.ClientSession

    def __init__(self, bot_configuration: BotConfiguration, network_configuration: NetworkConfiguration):
        debug_guilds = []
        if bot_configuration.get("debug_guild"):
            debug_guilds.append(bot_configuration["debug_guild"])

        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(debug_guilds=debug_guilds, auto_sync_commands=False, intents=intents)

        self.configuration = bot_configuration
        self.network_configuration = network_configuration

        self.add_listener(application_command_error, "on_application_command_error")
        self.load_extension("randovania.discord_bot.preset_lookup")
        self.load_extension("randovania.discord_bot.database_command")
        self.load_extension("randovania.discord_bot.faq_command")

    async def on_ready(self) -> None:
        token_hash = hashlib.sha256(self.configuration["token"].encode()).hexdigest()
        self.rdv_http = http_lib.http_session(headers=connection_headers())
        self.rdv_http.headers["X-Randovania-Discord-Bot"] = token_hash

        for cog in self.cogs.values():
            if isinstance(cog, RandovaniaCog):
                await cog.add_commands()

        for command in self.pending_application_commands:
            assert isinstance(command, discord.ApplicationCommand)
            if not isinstance(command, discord.SlashCommand):
                continue
            if command_prefix := self.configuration.get("command_prefix", ""):
                if not command.name.startswith(command_prefix):
                    command.name = command_prefix + command.name
            if "_" in command.name:
                command.name = command.name.replace("_", "-")

        await self.sync_commands()
        logging.info("Finished syncing commands.")


def run() -> None:
    network_config = randovania.get_configuration()
    bot_configuration = network_config["discord_bot"]

    client = RandovaniaBot(bot_configuration, network_config)
    client.run(bot_configuration["token"])
