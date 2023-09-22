from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest

from randovania.gui.dialog.login_prompt_dialog import LoginPromptDialog

if TYPE_CHECKING:
    import pytest_mock


@pytest.fixture(name="prompt")
def login_prompt_fixture(skip_qtbot):
    return LoginPromptDialog(MagicMock())


@pytest.mark.parametrize("valid_name", [False, True])
async def test_on_login_as_guest_button(prompt, mocker: pytest_mock.MockerFixture, valid_name):
    # Setup
    prompt.network_client.login_as_guest = AsyncMock()
    mock_prompt = mocker.patch("randovania.gui.dialog.text_prompt_dialog.TextPromptDialog.prompt", autospec=True)
    if not valid_name:
        mock_prompt.return_value = None

    # Run
    await prompt.on_login_as_guest_button()

    # Assert
    mock_prompt.assert_awaited_once_with(
        parent=prompt,
        title="Enter guest name",
        description="Select a name for the guest account:",
        is_modal=True,
    )
    if valid_name:
        prompt.network_client.login_as_guest.assert_awaited_once_with(mock_prompt.return_value)
    else:
        prompt.network_client.login_as_guest.assert_not_awaited()


async def test_on_login_with_discord_button(prompt):
    # Setup
    prompt.network_client.login_with_discord = AsyncMock()

    # Run
    await prompt.on_login_with_discord_button()

    # Assert
    prompt.network_client.login_with_discord.assert_awaited_once_with()
