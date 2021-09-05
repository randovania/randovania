import pytest
from mock import MagicMock, AsyncMock, call

import randovania
from randovania.games.game import RandovaniaGame
from randovania.server.discord import preset_lookup


@pytest.mark.asyncio
async def test_on_message_from_bot(mocker):
    mock_look_for: AsyncMock = mocker.patch("randovania.server.discord.preset_lookup.look_for_permalinks",
                                            new_callable=AsyncMock)
    client = MagicMock()
    cog = preset_lookup.PermalinkLookupCog(None, client)

    message = MagicMock()
    message.author = client.user

    # Run
    await cog.on_message(message)

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
    mock_look_for: AsyncMock = mocker.patch("randovania.server.discord.preset_lookup.look_for_permalinks",
                                            new_callable=AsyncMock)
    cog = preset_lookup.PermalinkLookupCog({"channel_name_filter": name_filter, "guild": guild}, MagicMock())

    message = MagicMock()
    message.channel.name = "the_expected_name"
    message.guild.id = 1234

    # Run
    await cog.on_message(message)

    # Assert
    if expected:
        mock_look_for.assert_awaited_once_with(message)
    else:
        mock_look_for.assert_not_awaited()


@pytest.mark.parametrize("is_solo", [False, True])
@pytest.mark.parametrize("has_multiple", [False, True])
@pytest.mark.asyncio
async def test_look_for_permalinks(mocker, is_solo, has_multiple):
    preset = MagicMock()
    preset.game = RandovaniaGame.METROID_PRIME_ECHOES
    permalink_1 = MagicMock()
    permalink_1.player_count = 1 if is_solo else 2
    permalink_1.get_preset.return_value = preset

    permalink_2 = MagicMock()
    embed = MagicMock()

    mock_embed: MagicMock = mocker.patch("discord.Embed", side_effect=[embed])

    mock_describe: MagicMock = mocker.patch("randovania.gui.lib.preset_describer.describe",
                                            return_value=[
                                                ("General", ["Foo", "Bar"]),
                                                ("Other", ["X", "Y"]),
                                            ])
    mock_from_str: MagicMock = mocker.patch(
        "randovania.layout.permalink.Permalink.from_str",
        side_effect=[permalink_1, permalink_2] if has_multiple else [permalink_1],
    )

    message = AsyncMock()
    if has_multiple:
        message.content = "yu4abbceWfLI- `yua73123yWdLI-` foo???"
    else:
        message.content = "yu4abbceWfLI- foo???"

    # Run
    await preset_lookup.look_for_permalinks(message)

    # Assert
    if has_multiple:
        mock_from_str.assert_has_calls([
            call("yu4abbceWfLI-"),
            call("yua73123yWdLI-"),
        ])
    else:
        mock_from_str.assert_called_once_with("yu4abbceWfLI-")

    if is_solo:
        permalink_1.get_preset.assert_called_once_with(0)
        mock_describe.assert_called_once_with(preset)
    else:
        permalink_1.get_preset.assert_not_called()
        mock_describe.assert_not_called()

    mock_embed.assert_called_once_with(
        title="`yu4abbceWfLI-`", description=f"{permalink_1.player_count} player multiworld permalink",
    )
    if is_solo:
        assert embed.description == "Metroid Prime 2: Echoes permalink for Randovania {}".format(randovania.VERSION)
        embed.add_field.assert_has_calls([
            call(name="General", value="Foo\nBar", inline=True),
            call(name="Other", value="X\nY", inline=True),
        ])

    content = None
    if has_multiple:
        content = "Multiple permalinks found, using only the first."
    message.reply.assert_awaited_once_with(
        content=content,
        embed=embed,
        mention_author=False,
    )


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
    await preset_lookup.reply_for_preset(message, versioned_preset)

    # Assert
    mock_embed.assert_called_once_with(title=preset.name, description=preset.description)
    embed.add_field.assert_has_calls([
        call(name="General", value="Foo\nBar", inline=True),
        call(name="Other", value="X\nY", inline=True),
    ])
    message.reply.assert_awaited_once_with(embed=embed, mention_author=False)
    mock_describe.assert_called_once_with(preset)
