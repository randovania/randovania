import logging

import discord

import randovania
from randovania.server.discord.randovania_cog import RandovaniaCog


async def application_command_error(ctx: discord.ApplicationContext, error: discord.DiscordException):
    logging.exception(
        "Exception when user %s used %s with args %s",
        str(ctx.user),
        ctx.command.qualified_name,
        str(ctx.selected_options),
        exc_info=error,
    )
    await ctx.respond("Sorry, an error has occurred processing the request.", ephemeral=True)


class RandovaniaBot(discord.Bot):
    def __init__(self, configuration: dict):
        debug_guilds = []
        if configuration.get("debug_guild"):
            debug_guilds.append(configuration["debug_guild"])

        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(debug_guilds=debug_guilds, auto_sync_commands=False, intents=intents)

        self.configuration = configuration
        self.add_listener(application_command_error, "on_application_command_error")
        self.load_extension("randovania.server.discord.preset_lookup")
        self.load_extension("randovania.server.discord.database_command")
        self.load_extension("randovania.server.discord.faq_command")

    async def on_ready(self):
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


def run():
    configuration = randovania.get_configuration()["discord_bot"]

    client = RandovaniaBot(configuration)
    client.run(configuration["token"])
