from unittest.mock import MagicMock, AsyncMock, ANY

import pytest

from randovania.games.game import RandovaniaGame
from randovania.server.discord.faq_command import FaqCommandCog


@pytest.mark.asyncio
async def test_on_ready():
    # Setup
    cog = FaqCommandCog({"guild": 1234}, MagicMock())
    slash = cog.bot.slash
    slash.add_subcommand = MagicMock()
    slash.sync_all_commands = AsyncMock()

    # Run
    await cog.on_ready()

    # Assert
    slash.add_subcommand.assert_called()
    slash.sync_all_commands.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_faq_game_command():
    # Setup
    cog = FaqCommandCog({}, MagicMock())
    slash = cog.bot.slash
    slash.sync_all_commands = AsyncMock()
    ctx = AsyncMock()

    # Run
    await cog.faq_game_command(ctx, RandovaniaGame.METROID_PRIME_ECHOES, "question_1")

    # Assert
    ctx.send.assert_awaited_once_with(
        content=f"Requested by {ctx.author.display_name}.\n**{RandovaniaGame.METROID_PRIME_ECHOES.long_name}**",
        embed=ANY,
    )
