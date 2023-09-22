from __future__ import annotations

from unittest.mock import ANY, AsyncMock, MagicMock

from randovania.games.game import RandovaniaGame
from randovania.server.discord.faq_command import FaqCommandCog, GameFaqMessage


async def test_add_commands():
    # Setup
    cog = FaqCommandCog({"guild": 1234}, MagicMock())

    # Run
    await cog.add_commands()

    # Assert
    cog.bot.create_group.assert_called_once_with("faq")
    cog.bot.create_group.return_value.subcommands.append.assert_called()


async def test_faq_game_command():
    # Setup
    message = GameFaqMessage(RandovaniaGame.METROID_PRIME_ECHOES)
    ctx = AsyncMock()

    # Run
    await message.callback(ctx, "question_1")

    # Assert
    ctx.respond.assert_awaited_once_with(
        content=f"Requested by {ctx.author.display_name}.\n**{RandovaniaGame.METROID_PRIME_ECHOES.long_name}**",
        embed=ANY,
    )
