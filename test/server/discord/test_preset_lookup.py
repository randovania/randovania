import subprocess
from unittest.mock import MagicMock, AsyncMock, call

import pytest

import randovania
from randovania.games.game import RandovaniaGame
from randovania.server.discord import preset_lookup


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


@pytest.mark.parametrize(["is_dev", "git_result", "expected_result"], [
    (False, "v3.2.2-902-gc361caae\n", None),
    (True, "v3.2.2-902-gc361caae\n", "3.3.0.dev902"),
    (False, "v4.0.0\n", "4.0.0"),
])
def test_get_version_success(mocker, is_dev, git_result, expected_result):
    mocker.patch("randovania.is_dev_version", return_value=is_dev)
    mocker.patch("subprocess.run", return_value=subprocess.CalledProcessError(0, [], output=git_result))
    result = preset_lookup.get_version("foo", b'J/A')
    assert result == expected_result


def test_get_version_failure_missing(mocker):
    mocker.patch("subprocess.run", side_effect=FileNotFoundError)
    result = preset_lookup.get_version("foo", b'J/A')
    assert result == f"(Unknown version: 4a2f41)"


def test_get_version_failure_unknown(mocker):
    mocker.patch("subprocess.run", side_effect=subprocess.CalledProcessError(0, []))
    result = preset_lookup.get_version("foo", b'J/A')
    assert result is None


@pytest.mark.parametrize("is_solo", [False, True])
@pytest.mark.parametrize("has_multiple", [False, True])
async def test_look_for_permalinks(mocker, is_solo, has_multiple):
    preset = MagicMock()
    preset.game = RandovaniaGame.METROID_PRIME_ECHOES
    permalink_1 = MagicMock()
    permalink_1.seed_hash = b"XXXXX"
    permalink_1.randovania_version = randovania.GIT_HASH
    permalink_1.parameters.player_count = 1 if is_solo else 2
    permalink_1.parameters.get_preset.return_value = preset
    permalink_1.parameters.presets = [preset] if is_solo else [preset, preset]
    permalink_2 = MagicMock()
    permalink_2.randovania_version = randovania.GIT_HASH
    embed = MagicMock()

    mock_embed: MagicMock = mocker.patch("discord.Embed", side_effect=[embed])
    mock_create_actionrow = mocker.patch("discord_slash.utils.manage_components.create_actionrow")

    mock_describe: MagicMock = mocker.patch("randovania.layout.preset_describer.describe",
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
        permalink_1.parameters.get_preset.assert_called_once_with(0)
        mock_describe.assert_called_once_with(preset)
    else:
        permalink_1.parameters.get_preset.assert_not_called()
        mock_describe.assert_not_called()

    mock_embed.assert_called_once_with(
        title="`yu4abbceWfLI-`", description=f"{permalink_1.parameters.player_count} player multiworld permalink",
    )
    suffix = f"Seed Hash: Elevator Key Checkpoint (LBMFQWCY)"
    if is_solo:
        split_desc = embed.description.split("\n")
        split_desc[0] = split_desc[0].split(" for Randovania")[0]
        assert split_desc == ["Metroid Prime 2: Echoes permalink", suffix]
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
        components=[mock_create_actionrow.return_value],
        mention_author=False,
    )


async def test_reply_for_preset(mocker):
    mock_describe: MagicMock = mocker.patch("randovania.layout.preset_describer.describe",
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
