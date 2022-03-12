from discord.ext import commands
from discord_slash import SlashCommand


class RandovaniaCog(commands.Cog):
    async def add_commands(self, slash: SlashCommand):
        raise NotImplementedError()
