import pytest
from mock import MagicMock, AsyncMock

from randovania.gui.dialog.login_prompt_dialog import LoginPromptDialog


@pytest.fixture(name="prompt")
def login_prompt_fixture(skip_qtbot):
    return LoginPromptDialog(MagicMock())


@pytest.mark.asyncio
async def test_on_login_as_guest_button(prompt, mocker):
    # Setup
    prompt.network_client.login_as_guest = AsyncMock()
    mock_dialog = mocker.patch("PySide2.QtWidgets.QInputDialog").return_value
    mock_execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock,
                                       return_value=mock_dialog.Accepted)

    # Run
    await prompt.on_login_as_guest_button()

    # Assert
    mock_execute_dialog.assert_awaited_once_with(mock_dialog)
    prompt.network_client.login_as_guest.assert_awaited_once_with(mock_dialog.textValue.return_value)


@pytest.mark.asyncio
async def test_on_login_with_discord_button(prompt):
    # Setup
    prompt.network_client.login_with_discord = AsyncMock()

    # Run
    await prompt.on_login_with_discord_button()

    # Assert
    prompt.network_client.login_with_discord.assert_awaited_once_with()
