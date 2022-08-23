import discord

from randovania.games.game import RandovaniaGame
from randovania.lib import enum_lib
from randovania.server.discord.bot import RandovaniaBot
from randovania.server.discord.randovania_cog import RandovaniaCog


async def game_faq_entry(context: discord.ApplicationContext, question):
    raise RuntimeError("Should not be called")


def _shorten(n: str) -> str:
    if len(n) > 100:
        return n[:97] + "..."
    return n


class GameFaqMessage:
    def __init__(self, game: RandovaniaGame):
        self.game = game

    def create_command(self, parent) -> discord.SlashCommand:
        result = discord.SlashCommand(
            game_faq_entry,
            name=self.game.value,
            description=f"Prints the answer to a FAQ for {self.game.long_name}.",
            parent=parent,
            options=[discord.Option(
                input_type=str,
                name="question",
                description="Which question to answer?",
                required=True,
                choices=[
                    discord.OptionChoice(name=_shorten(question), value=f"question_{question_id}")
                    for question_id, (question, answer) in enumerate(list(self.game.data.faq))
                ]
            )],
        )
        result.callback = self.callback
        return result

    async def callback(self, context: discord.ApplicationContext, question: str):
        for qid, (question_text, answer) in enumerate(self.game.data.faq):
            if f"question_{qid}" == question:
                await context.respond(
                    content=f"Requested by {context.author.display_name}.\n**{self.game.long_name}**",
                    embed=discord.Embed(
                        title=question_text,
                        description=answer,
                    )
                )
                return

        await context.respond(content="Unknown question.", hidden=True)


class FaqCommandCog(RandovaniaCog):
    def __init__(self, configuration: dict, bot: RandovaniaBot):
        self.configuration = configuration
        self.bot = bot

    async def add_commands(self):
        base_command = self.configuration.get("command_prefix", "") + "randovania-faq"

        group = self.bot.create_group(
            base_command
        )

        for game in enum_lib.iterate_enum(RandovaniaGame):
            faq_entries = list(game.data.faq)
            if not faq_entries:
                continue

            faq_message = GameFaqMessage(game)
            group.subcommands.append(faq_message.create_command(group))


def setup(bot: RandovaniaBot):
    bot.add_cog(FaqCommandCog(bot.configuration, bot))
