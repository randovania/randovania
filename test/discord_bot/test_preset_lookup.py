from __future__ import annotations

import dataclasses
import subprocess
from typing import TYPE_CHECKING
from unittest.mock import ANY, AsyncMock, MagicMock, call

import discord
import pytest

import randovania
from randovania.game.game_enum import RandovaniaGame
from randovania.layout.layout_description import LayoutDescription

if TYPE_CHECKING:
    import pytest_mock


async def test_get_presets_from_message(mocker: pytest_mock.MockerFixture) -> None:
    a1 = MagicMock(spec=discord.Attachment)
    a1.filename = "thing.json"
    a2 = MagicMock(spec=discord.Attachment)
    a2.filename = "p1.rdvpreset"
    a2.read = AsyncMock(return_value=b"")
    a3 = MagicMock(spec=discord.Attachment)
    a3.filename = "p2.rdvpreset"
    a3.read = AsyncMock(return_value=b"2")

    message = MagicMock()
    message.reply = AsyncMock()
    message.attachments = [
        a1,
        a2,
        a3,
    ]

    mock_embed = mocker.patch("discord.Embed")
    mock_get_preset = mocker.patch("randovania.layout.versioned_preset.VersionedPreset.get_preset")

    from randovania.discord_bot import preset_lookup

    results = [t async for t in preset_lookup._get_presets_from_message(message)]

    assert results == [mock_get_preset.return_value]
    mock_embed.assert_called_once_with(
        title="Unable to process `p1.rdvpreset`",
        description="Expecting value: line 1 column 1 (char 0)",
    )
    message.reply.assert_awaited_once_with(
        embed=mock_embed.return_value,
        mention_author=False,
    )
    mock_get_preset.assert_called_once_with()


@pytest.mark.parametrize("reason", ["from_bot", "no_permission", "ok"])
async def test_on_message(mocker, reason: str):
    mock_look_for: AsyncMock = mocker.patch(
        "randovania.discord_bot.preset_lookup.look_for_permalinks", new_callable=AsyncMock
    )
    client = MagicMock()

    from randovania.discord_bot import preset_lookup

    cog = preset_lookup.PermalinkLookupCog(None, client)

    message = MagicMock()
    message.channel = MagicMock(spec=discord.TextChannel)
    message.channel.permissions_for.return_value.send_messages = reason != "no_permission"

    if reason == "from_bot":
        message.author = client.user

    # Run
    await cog.on_message(message)

    # Assert
    if reason != "ok":
        mock_look_for.assert_not_awaited()
    else:
        mock_look_for.assert_awaited_once_with(message)


@pytest.mark.parametrize(
    ("is_dev", "git_result", "expected_result"),
    [
        (False, "v3.2.2-902-gc361caae\n", None),
        (True, "v3.2.2-902-gc361caae\n", "3.3.0.dev902"),
        (False, "v4.0.0\n", "4.0.0"),
    ],
)
def test_get_version_success(mocker, is_dev, git_result, expected_result):
    mocker.patch("randovania.is_dev_version", return_value=is_dev)
    mocker.patch("subprocess.run", return_value=subprocess.CalledProcessError(0, [], output=git_result))
    from randovania.discord_bot import preset_lookup

    result = preset_lookup.get_version("foo", b"J/A")
    assert result == expected_result


def test_get_version_failure_missing(mocker):
    mocker.patch("subprocess.run", side_effect=FileNotFoundError)
    from randovania.discord_bot import preset_lookup

    result = preset_lookup.get_version("foo", b"J/A")
    assert result == "(Unknown version: 4a2f41)"


def test_get_version_failure_unknown(mocker):
    mocker.patch("subprocess.run", side_effect=subprocess.CalledProcessError(0, []))
    from randovania.discord_bot import preset_lookup

    result = preset_lookup.get_version("foo", b"J/A")
    assert result is None


@pytest.mark.parametrize("is_solo", [False, True])
@pytest.mark.parametrize("has_multiple", [False, True])
async def test_look_for_permalinks(mocker, is_solo, has_multiple, is_dev_version):
    preset = MagicMock()
    preset.game = RandovaniaGame.METROID_PRIME_ECHOES
    permalink_1 = MagicMock()
    permalink_1.seed_hash = b"XXXXX"
    permalink_1.randovania_version = randovania.GIT_HASH
    permalink_1.parameters.world_count = 1 if is_solo else 2
    permalink_1.parameters.get_preset.return_value = preset
    permalink_1.parameters.presets = [preset] if is_solo else [preset, preset]
    permalink_2 = MagicMock()
    permalink_2.randovania_version = randovania.GIT_HASH
    embed = MagicMock()

    mock_embed: MagicMock = mocker.patch("discord.Embed", side_effect=[embed])
    mock_create_actionrow = mocker.patch("randovania.discord_bot.preset_lookup.RequestPresetsView")

    if is_dev_version:
        mocked_git_describe = "v4.0.0-123"
        mocked_rdv_version = "4.1.0.dev123"
    else:
        mocked_git_describe = "v4.0.0"
        mocked_rdv_version = "4.0.0"

    mocker.patch("randovania.discord_bot.preset_lookup._git_describe", return_value=mocked_git_describe)

    mock_describe: MagicMock = mocker.patch(
        "randovania.layout.preset_describer.describe",
        return_value=[
            ("General", ["Foo", "Bar"]),
            ("Other", ["X", "Y"]),
        ],
    )
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
    from randovania.discord_bot import preset_lookup

    await preset_lookup.look_for_permalinks(message)

    # Assert
    # mock_git_describe.assert_called()

    if has_multiple:
        mock_from_str.assert_has_calls(
            [
                call("yu4abbceWfLI-"),
                call("yua73123yWdLI-"),
            ]
        )
    else:
        mock_from_str.assert_called_once_with("yu4abbceWfLI-")

    if is_solo:
        permalink_1.parameters.get_preset.assert_called_once_with(0)
        mock_describe.assert_called_once_with(preset)
    else:
        permalink_1.parameters.get_preset.assert_not_called()
        mock_describe.assert_not_called()

    mock_embed.assert_called_once_with(
        title="`yu4abbceWfLI-`",
        description=f"{permalink_1.parameters.world_count} player multiworld permalink",
    )
    suffix = "Seed Hash: Echo Junction Charge (LBMFQWCY)"
    if is_solo:
        split_desc = embed.description.split("\n")
        assert split_desc == [f"Metroid Prime 2: Echoes permalink for Randovania {mocked_rdv_version}", suffix]
        embed.add_field.assert_has_calls(
            [
                call(name="General", value="Foo\nBar", inline=True),
                call(name="Other", value="X\nY", inline=True),
            ]
        )

    content = None
    if has_multiple:
        content = "Multiple permalinks found, using only the first."

    message.reply.assert_awaited_once_with(
        content=content,
        embed=embed,
        view=mock_create_actionrow.return_value,
        mention_author=False,
    )


async def test_reply_for_preset(mocker):
    mock_describe: MagicMock = mocker.patch(
        "randovania.layout.preset_describer.describe",
        return_value=[
            ("General", ["Foo", "Bar"]),
            ("Other", ["X", "Y"]),
        ],
    )
    message = AsyncMock()
    preset = MagicMock()
    embed = MagicMock()

    mock_embed: MagicMock = mocker.patch("discord.Embed", side_effect=[embed])

    # Run
    from randovania.discord_bot import preset_lookup

    await preset_lookup.reply_for_preset(message, preset)

    # Assert
    mock_embed.assert_called_once_with(title=preset.name, description=f"{preset.game.long_name}\n{preset.description}")
    embed.add_field.assert_has_calls(
        [
            call(name="General", value="Foo\nBar", inline=True),
            call(name="Other", value="X\nY", inline=True),
        ]
    )
    message.reply.assert_awaited_once_with(embed=embed, mention_author=False)
    mock_describe.assert_called_once_with(preset)


@pytest.mark.parametrize("has_spoiler", [False, True])
async def test_reply_for_layout_description(mocker: pytest_mock.MockerFixture, test_files_dir, has_spoiler):
    mocker.patch("randovania.layout.layout_description.shareable_word_hash", return_value="<WORD HASH>")

    message = AsyncMock()
    layout = LayoutDescription.from_file(test_files_dir.joinpath("log_files", "blank", "issue-3717.rdvgame"))
    layout = dataclasses.replace(
        layout,
        generator_parameters=dataclasses.replace(
            layout.generator_parameters,
            spoiler=has_spoiler,
        ),
    )

    # Run
    from randovania.discord_bot import preset_lookup

    await preset_lookup.reply_for_layout_description(message, layout)

    # Assert
    expected_description = [
        "Blank Development Game, with preset Starter Preset.",
        f"Seed Hash for {randovania.VERSION}: <WORD HASH>",
    ]
    if not has_spoiler:
        expected_description.insert(1, "**For Races** (No Spoiler available).")

    message.reply.assert_awaited_once_with(embed=ANY, mention_author=False)
    embed: discord.Embed = message.reply.call_args.kwargs["embed"]
    assert embed.title == "Spoiler file (Generated with 5.1.0.dev64)"
    assert embed.description == "\n".join(expected_description)
    fields = [field.to_dict() for field in embed.fields]
    assert fields == [
        {"name": "Logic Settings", "value": "All tricks disabled", "inline": True},
        {
            "name": "Pickup Pool",
            "value": "Size: 5 of 8\nUnmodified starting pickup\nExcludes Health\nShuffles 0x Progressive Jump",
            "inline": True,
        },
        {"name": "Gameplay", "value": "Starts at Intro - Starting Area", "inline": True},
    ]
