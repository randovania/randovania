from unittest.mock import MagicMock, AsyncMock, ANY

from randovania.games.game import RandovaniaGame
from randovania.server.discord.faq_command import FaqCommandCog


async def test_add_commands():
    # Setup
    cog = FaqCommandCog({"guild": 1234}, MagicMock())
    slash = cog.bot.slash
    slash.add_subcommand = MagicMock()

    # Run
    await cog.add_commands(slash)

    # Assert
    slash.add_subcommand.assert_called()


async def test_faq_game_command():
    # Setup
    cog = FaqCommandCog({}, MagicMock())
    ctx = AsyncMock()

    # Run
    await cog.faq_game_command(ctx, RandovaniaGame.METROID_PRIME_ECHOES, "question_1")

    # Assert
    ctx.send.assert_awaited_once_with(
        content=f"Requested by {ctx.author.display_name}.\n**{RandovaniaGame.METROID_PRIME_ECHOES.long_name}**",
        embed=ANY,
    )
