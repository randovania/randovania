from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from randovania.server.discord import bot


async def test_on_ready():
    b = bot.RandovaniaBot({"command_prefix": "prefix-"})
    assert len(b.extensions) == 3

    b.sync_commands = AsyncMock()
    await b.on_ready()

    b.sync_commands.assert_awaited_once_with()
    assert [c.name for c in b.pending_application_commands] == [
        "Generate new game",
        "prefix-database",
        "prefix-website",
        "prefix-faq",
    ]


def test_run(mocker):
    config = MagicMock()
    mocker.patch(
        "randovania.get_configuration",
        return_value={
            "discord_bot": config,
        },
    )
    mock_bot_class = mocker.patch("randovania.server.discord.bot.RandovaniaBot")

    # Run
    bot.run()

    # Assert
    mock_bot_class.assert_called_once_with(config)
    mock_bot_class.return_value.run.assert_called_once_with(config["token"])
