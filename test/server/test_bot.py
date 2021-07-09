import pytest
from mock import MagicMock, AsyncMock, call

import randovania
from randovania.games.game import RandovaniaGame
from randovania.server import bot


@pytest.mark.asyncio
async def test_on_message_from_bot(mocker):
    mock_look_for: AsyncMock = mocker.patch("randovania.server.bot.look_for_permalinks", new_callable=AsyncMock)
    client = bot.Bot(None)

    message = MagicMock()
    message.author = client.user

    # Run
    await client.on_message(message)

    # Assert
    mock_look_for.assert_not_awaited()


@pytest.mark.parametrize(["name_filter", "guild", "expected"], [
    ("unknown", 0, False),
    ("expected_name", 0, False),
    ("unknown", 1234, False),
    ("expected_name", 1234, True),
])
@pytest.mark.asyncio
async def test_on_message_wrong_place(mocker, name_filter: str, guild: int, expected):
    mock_look_for: AsyncMock = mocker.patch("randovania.server.bot.look_for_permalinks", new_callable=AsyncMock)
    client = bot.Bot({"channel_name_filter": name_filter, "guild": guild})

    message = MagicMock()
    message.channel.name = "the_expected_name"
    message.guild.id = 1234

    # Run
    await client.on_message(message)

    # Assert
    if expected:
        mock_look_for.assert_awaited_once_with(message.content, message.channel)
    else:
        mock_look_for.assert_not_awaited()


@pytest.mark.asyncio
async def test_look_for_permalinks(mocker):
    permalink_1 = MagicMock()
    permalink_1.player_count = 2

    preset = MagicMock()
    preset.game = RandovaniaGame.METROID_PRIME_ECHOES
    permalink_2 = MagicMock()
    permalink_2.player_count = 1
    permalink_2.get_preset.return_value = preset

    embed_1 = MagicMock()
    embed_2 = MagicMock()

    mock_embed: MagicMock = mocker.patch("discord.Embed", side_effect=[embed_1, embed_2])

    mock_describe: MagicMock = mocker.patch("randovania.gui.lib.preset_describer.describe",
                                            return_value=[
                                                ("General", ["Foo", "Bar"]),
                                                ("Other", ["X", "Y"]),
                                            ])
    mock_from_str: MagicMock = mocker.patch("randovania.layout.permalink.Permalink.from_str",
                                            side_effect=[permalink_1, permalink_2])

    channel = AsyncMock()
    message = "yu4abbceWfLI- `yua73123yWdLI-` foo???"

    # Run
    await bot.look_for_permalinks(message, channel)

    # Assert
    mock_from_str.assert_has_calls([
        call("yu4abbceWfLI-"),
        call("yua73123yWdLI-"),
    ])
    permalink_2.get_preset.assert_called_once_with(0)
    mock_describe.assert_called_once_with(preset)

    mock_embed.assert_has_calls([
        call(title="yu4abbceWfLI-", description="2 player multiworld permalink"),
        call(title="yua73123yWdLI-", description="1 player multiworld permalink"),
    ])
    embed_1.add_field.assert_not_called()
    assert embed_2.description == "Metroid Prime 2: Echoes permalink for Randovania {}".format(randovania.VERSION)
    embed_2.add_field.assert_has_calls([
        call(name="General", value="Foo\nBar", inline=True),
        call(name="Other", value="X\nY", inline=True),
    ])
    channel.send.assert_has_awaits([
        call(embed=embed_1),
        call(embed=embed_2),
    ])


@pytest.mark.asyncio
async def test_reply_for_preset(mocker):
    mock_describe: MagicMock = mocker.patch("randovania.gui.lib.preset_describer.describe",
                                            return_value=[
                                                ("General", ["Foo", "Bar"]),
                                                ("Other", ["X", "Y"]),
                                            ])
    message = AsyncMock()
    versioned_preset = MagicMock()
    preset = versioned_preset.get_preset.return_value
    embed = MagicMock()

    mock_embed: MagicMock = mocker.patch("discord.Embed", side_effect=[embed])

    # Run
    await bot.reply_for_preset(message, versioned_preset)

    # Assert
    mock_embed.assert_called_once_with(title=preset.name, description=preset.description)
    embed.add_field.assert_has_calls([
        call(name="General", value="Foo\nBar", inline=True),
        call(name="Other", value="X\nY", inline=True),
    ])
    message.reply.assert_awaited_once_with(embed=embed)
    mock_describe.assert_called_once_with(preset)
