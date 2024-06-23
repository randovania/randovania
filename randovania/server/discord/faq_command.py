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
            description=f"{self.game.long_name} frequently asked questions.",
            parent=parent,
            options=[
                discord.Option(
                    input_type=str,
                    name="question",
                    description="Which question to answer?",
                    required=True,
                    choices=[
                        discord.OptionChoice(name=_shorten(question), value=f"question_{question_id}")
                        for question_id, (question, answer) in enumerate(list(self.game.data.faq))
                    ],
                )
            ],
        )
        result.cog = None
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
                    ),
                )
                return

        await context.respond(content="Unknown question.", hidden=True)


class FaqCommandCog(RandovaniaCog):
    def __init__(self, configuration: dict, bot: RandovaniaBot):
        self.configuration = configuration
        self.bot = bot

    @discord.commands.slash_command()
    async def website(self, context: discord.ApplicationContext):
        """Posts information about Randovania's website."""
        embed = discord.Embed(
            title="https://randovania.org/",
            description=(
                "In the website, you'll find download links to Randovania and instructions on how to get started!"
            ),
        )
        await context.respond(embed=embed)

    async def add_commands(self):
        base_command = self.configuration.get("command_prefix", "") + "faq"

        group = self.bot.create_group(base_command)

        for game in enum_lib.iterate_enum(RandovaniaGame):
            faq_entries = list(game.data.faq)
            if not faq_entries or not game.data.development_state.can_view():
                continue

            faq_message = GameFaqMessage(game)
            group.subcommands.append(faq_message.create_command(group))


def setup(bot: RandovaniaBot):
    bot.add_cog(FaqCommandCog(bot.configuration, bot))
