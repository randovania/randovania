import functools

import discord
from discord_slash import SlashContext, SlashCommandOptionType, SlashCommand
from discord_slash.utils import manage_commands

from randovania.games.game import RandovaniaGame
from randovania.lib import enum_lib
from randovania.server.discord.bot import RandovaniaBot
from randovania.server.discord.randovania_cog import RandovaniaCog


class FaqCommandCog(RandovaniaCog):
    def __init__(self, configuration: dict, bot: RandovaniaBot):
        self.configuration = configuration
        self.bot = bot

    async def add_commands(self, slash: SlashCommand):
        base_command = self.configuration.get("command_prefix", "") + "randovania-faq"

        for game in enum_lib.iterate_enum(RandovaniaGame):
            faq_entries = list(game.data.faq)
            if not faq_entries:
                continue

            def _shorten(n: str) -> str:
                if len(n) > 100:
                    return n[:97] + "..."
                return n

            slash.add_subcommand(
                functools.partial(self.faq_game_command, game=game),
                base_command,
                name=game.value,
                description=f"Prints the answer to a FAQ for {game.long_name}.",
                options=[
                    manage_commands.create_option(
                        "question", "Which question to answer?",
                        option_type=SlashCommandOptionType.STRING,
                        required=True,
                        choices=[
                            manage_commands.create_choice(f"question_{question_id}", _shorten(question))
                            for question_id, (question, answer) in enumerate(faq_entries)
                        ]
                    )
                ],
            )

    async def faq_game_command(self, ctx: SlashContext, game: RandovaniaGame, question: str):
        for qid, (question_text, answer) in enumerate(game.data.faq):
            if f"question_{qid}" == question:
                await ctx.send(
                    content=f"Requested by {ctx.author.display_name}.\n**{game.long_name}**",
                    embed=discord.Embed(
                        title=question_text,
                        description=answer,
                    )
                )
                return

        await ctx.send(content="Unknown question.", hidden=True)


def setup(bot: RandovaniaBot):
    bot.add_cog(FaqCommandCog(bot.configuration, bot))
