import logging

import discord.ext.commands
from discord_slash import SlashCommand

import randovania
from randovania.server.discord.randovania_cog import RandovaniaCog


class RandovaniaBot(discord.ext.commands.Bot):
    def __init__(self, configuration: dict):
        super().__init__("%unused-prefix%")
        self.slash = SlashCommand(
            self,
            debug_guild=configuration["debug_guild"],
        )
        self.configuration = configuration
        self.load_extension("randovania.server.discord.preset_lookup")
        self.load_extension("randovania.server.discord.database_command")
        self.load_extension("randovania.server.discord.faq_command")

    async def on_ready(self):
        for cog in self.cogs.values():
            if isinstance(cog, RandovaniaCog):
                await cog.add_commands(self.slash)

        await self.slash.sync_all_commands()


def run():
    configuration = randovania.get_configuration()["discord_bot"]

    client = RandovaniaBot(configuration)
    client.run(configuration["token"])
