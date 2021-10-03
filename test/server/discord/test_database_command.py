from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, ANY, call

import pytest
from discord_slash import ComponentType

from randovania.games.game import RandovaniaGame
from randovania.server.discord.database_command import DatabaseCommandCog, SplitWorld


@pytest.mark.asyncio
async def test_on_ready():
    # Setup
    cog = DatabaseCommandCog({"guild": 1234}, MagicMock())
    slash = cog.bot.slash
    slash.sync_all_commands = AsyncMock()

    # Run
    await cog.on_ready()

    # Assert
    slash.add_slash_command.assert_called_once_with(
        cog.database_command,
        name="database-inspect",
        description="Consult the Randovania's logic database for one specific room.",
        guild_ids=[1234],
        options=[ANY],
    )
    slash.add_component_callback.assert_called_once_with(
        cog.on_database_component,
        components=ANY,
        use_callback_name=False,
    )
    slash.sync_all_commands.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_database_command():
    # Setup
    cog = DatabaseCommandCog({"guild": 1234}, MagicMock())

    area = MagicMock()
    area.name = "The Area"
    cog._split_worlds[RandovaniaGame.METROID_PRIME_CORRUPTION] = [
        SplitWorld(MagicMock(), "The World", [area]),
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
        SplitWorld(MagicMock(), "The World", [area]),
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
async def test_on_database_area_selected(echoes_game_description, mocker):
    # Setup
    mock_file: MagicMock = mocker.patch("discord.File")
    mock_digraph: MagicMock = mocker.patch("graphviz.Digraph")
    dot: MagicMock = mock_digraph.return_value
    dot.render.return_value = "bar"
    Path("bar").write_bytes(b"1234")

    cog = DatabaseCommandCog({"guild": 1234}, MagicMock())

    ctx = AsyncMock()
    ctx.selected_options = [f"area_1"]

    world = echoes_game_description.world_list.worlds[2]
    area = world.areas[0]
    split_world = SplitWorld(world, "The World", [MagicMock(), area])

    # Run
    await cog.on_database_area_selected(ctx, RandovaniaGame.METROID_PRIME_ECHOES, split_world, 2)

    # Assert
    ctx.send.assert_awaited_once_with(
        content=f"Requested by {ctx.author.display_name}.",
        embed=ANY,
        files=[mock_file.return_value],
        components=[ANY],
    )
    mock_digraph.assert_called_once_with(comment=area.name)
    dot.node.assert_has_calls([
        call(node.name)
        for node in area.nodes
    ])
    dot.render.assert_called_once_with(format="png", cleanup=True)
    mock_file.assert_called_once_with(Path("bar"))
    assert not Path("bar").is_file()


@pytest.mark.asyncio
async def test_on_area_node_selection(echoes_game_description, mocker):
    # Setup
    mock_embed: MagicMock = mocker.patch("discord.Embed")

    cog = DatabaseCommandCog({"guild": 1234}, MagicMock())

    world = echoes_game_description.world_list.worlds[2]
    area = world.areas[2]

    ctx = AsyncMock()
    ctx.selected_options = [area.nodes[0].name, area.nodes[2].name]

    # Run
    await cog.on_area_node_selection(ctx, RandovaniaGame.METROID_PRIME_ECHOES, area)

    # Assert
    ctx.edit_origin.assert_awaited_once_with(embed=mock_embed.return_value)
    mock_embed.assert_called_once_with(title=ctx.origin_message.embeds[0].title)
    mock_embed.return_value.add_field.assert_has_calls([
        call(
            name=area.nodes[0].name,
            value=ANY,
            inline=False,
        ),
        call(
            name=area.nodes[2].name,
            value=ANY,
            inline=False,
        ),
    ])
