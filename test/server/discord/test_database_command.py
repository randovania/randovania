import io
import os
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, ANY, call

import discord

from randovania.games.game import RandovaniaGame
from randovania.server.discord.database_command import DatabaseCommandCog, SplitWorld, SelectSplitWorldItem, \
    SelectAreaItem, AreaWidget, SelectNodesItem


async def test_add_commands():
    # Setup
    cog = DatabaseCommandCog({"guild": 1234}, MagicMock())

    # Run
    await cog.add_commands()

    # Assert
    command = cog.get_commands()[0]
    assert isinstance(command, discord.SlashCommand)
    assert command.name == "database"
    assert command.description == "Consult the Randovania's logic database for one specific room."


async def test_database_command():
    # Setup
    cog = DatabaseCommandCog({"guild": 1234}, MagicMock())
    cog.database_inspect.cog = cog
    cog._select_split_world_view[RandovaniaGame.METROID_PRIME_CORRUPTION] = view = MagicMock()
    ctx = AsyncMock()

    # Run
    await cog.database_inspect(ctx, game=RandovaniaGame.METROID_PRIME_CORRUPTION)

    # Assert
    ctx.respond.assert_awaited_once_with(
        embed=ANY,
        view=view,
        ephemeral=True,
    )


async def test_on_database_world_selected():
    # Setup
    area = MagicMock()
    area.area.name = "The Area"

    view = MagicMock()
    item = SelectSplitWorldItem(
        RandovaniaGame.METROID_PRIME_CORRUPTION,
        [
            SplitWorld(
                MagicMock(),
                "The World",
                [area],
                f"{RandovaniaGame.METROID_PRIME_CORRUPTION.value}_world_1",
                view,
            )
        ]
    )

    ctx = AsyncMock()
    ctx.response = MagicMock(spec=discord.InteractionResponse)
    item._selected_values = [f"{RandovaniaGame.METROID_PRIME_CORRUPTION.value}_world_1"]

    # Run
    await item.callback(ctx)

    # Assert
    ctx.edit_original_response.assert_awaited_once_with(
        embed=ANY,
        view=view,
    )


async def test_on_database_area_selected(tmp_path, echoes_game_description, mocker):
    # Setup
    mocker.patch("tempfile.mkdtemp", return_value=os.fspath(tmp_path))
    mock_file: MagicMock = mocker.patch("discord.File")
    mock_digraph: MagicMock = mocker.patch("graphviz.Digraph")
    dot: MagicMock = mock_digraph.return_value
    dot.render.return_value = os.fspath(tmp_path / "bar")
    Path(tmp_path / "bar").write_bytes(b"1234")

    db = echoes_game_description
    world = echoes_game_description.world_list.worlds[2]
    area = world.areas[0]
    view = MagicMock()

    split_world = SplitWorld(
        world, "The World",
        [MagicMock(),
         AreaWidget(area, "area_1", view)
         ],
        "split_world",
    )

    item = SelectAreaItem(RandovaniaGame.METROID_PRIME_ECHOES, split_world)

    ctx = AsyncMock()
    ctx.response = AsyncMock(spec=discord.InteractionResponse)
    item._selected_values = [f"area_1"]

    # Run
    await item.callback(ctx)

    # Assert
    ctx.response.send_message.assert_awaited_once_with(
        content=f"**{db.game.long_name}: {db.world_list.area_name(area)}**\nRequested by {ctx.user.display_name}.",
        files=[mock_file.return_value],
        view=view,
    )
    mock_digraph.assert_called_once_with(comment=area.name)
    dot.node.assert_has_calls([
        call(node.name)
        for node in area.nodes
        if not node.is_derived_node
    ])
    dot.render.assert_called_once_with(directory=os.fspath(tmp_path), format="png", cleanup=True)
    mock_file.assert_called_once_with(ANY, filename=f"{area.name}_graph.png")
    v = mock_file.call_args[0][0]
    assert isinstance(v, io.BytesIO)
    assert v.getvalue() == b"1234"
    assert not tmp_path.exists()


async def test_on_area_node_selection(echoes_game_description, mocker):
    # Setup
    mock_embed: MagicMock = mocker.patch("discord.Embed")

    world = echoes_game_description.world_list.worlds[2]
    area = world.areas[2]
    area_widget = AreaWidget(
        area,
        "command",
    )

    item = SelectNodesItem(RandovaniaGame.METROID_PRIME_ECHOES, area_widget)

    ctx = AsyncMock()
    ctx.response = AsyncMock(spec=discord.InteractionResponse)
    item._selected_values = [area.nodes[0].name, area.nodes[2].name]

    original_response = ctx.original_response.return_value

    # Run
    await item.callback(ctx)

    # Assert
    ctx.original_response.assert_awaited_once_with()
    original_response.edit.assert_awaited_once_with(embeds=[mock_embed.return_value, mock_embed.return_value])
    mock_embed.assert_has_calls([
        call(title=area.nodes[0].name,
             description=ANY),
        call(title=area.nodes[2].name,
             description=ANY),
    ])
