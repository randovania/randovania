from unittest.mock import MagicMock, AsyncMock, ANY

import pytest
from discord import Embed
from discord_slash import ComponentType

from randovania.games.game import RandovaniaGame
from randovania.server.discord.database_command import DatabaseCommandCog


@pytest.mark.asyncio
async def test_on_ready():
    # Setup
    cog = DatabaseCommandCog({"guild": 1234}, MagicMock())
    cog.slash = AsyncMock()

    # Run
    await cog.on_ready()

    # Assert
    cog.slash.add_slash_command.assert_called_once_with(
        cog.database_command,
        name="database-inspect",
        description="Consult the Randovania's logic database for one specific room.",
        guild_ids=[1234],
        options=[ANY],
    )
    cog.slash.add_component_callback.assert_called_once_with(
        cog.on_database_component,
        components=ANY,
        use_callback_name=False,
    )
    cog.slash.sync_all_commands.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_database_command():
    # Setup
    cog = DatabaseCommandCog({"guild": 1234}, MagicMock())

    area = MagicMock()
    area.name = "The Area"
    cog._split_worlds[RandovaniaGame.METROID_PRIME_CORRUPTION] = [
        (MagicMock(), "The World", [area]),
    ]

    ctx = AsyncMock()

    # Run
    await cog.database_command(ctx, RandovaniaGame.METROID_PRIME_CORRUPTION.value)

    # Assert
    ctx.send.assert_awaited_once_with(
        embed=ANY, components=ANY, hidden=True
    )


@pytest.mark.asyncio
async def test_on_database_world_selected():
    # Setup
    cog = DatabaseCommandCog({"guild": 1234}, MagicMock())

    area = MagicMock()
    area.name = "The Area"
    cog._split_worlds[RandovaniaGame.METROID_PRIME_CORRUPTION] = [
        tuple(),
        (MagicMock(), "The World", [area]),
    ]

    ctx = AsyncMock()
    ctx.selected_options = [f"{RandovaniaGame.METROID_PRIME_CORRUPTION.value}_world_1"]

    # Run
    await cog.on_database_world_selected(ctx, RandovaniaGame.METROID_PRIME_CORRUPTION)

    # Assert
    ctx.edit_origin.assert_awaited_once_with(
        embed=ANY,
        components=[
            ANY,
            {"type": ComponentType.actionrow, "components": ANY},
        ],
    )


@pytest.mark.asyncio
async def test_on_database_area_selected(echoes_game_description):
    # Setup
    cog = DatabaseCommandCog({"guild": 1234}, MagicMock())

    ctx = AsyncMock()
    ctx.selected_options = [f"area_1"]

    world = echoes_game_description.world_list.worlds[2]
    area = world.areas[0]
    split_world = (world, "The World", [MagicMock(), area])

    # Run
    await cog.on_database_area_selected(ctx, RandovaniaGame.METROID_PRIME_ECHOES, split_world)

    # Assert
    ctx.send.assert_awaited_once_with(embed=ANY)

