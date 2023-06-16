from unittest.mock import AsyncMock, MagicMock, ANY

import pytest
from PySide6 import QtWidgets
from pytest_mock import MockerFixture

from randovania.gui.lib import multiplayer_session_api
from randovania.network_client.network_client import UnableToConnect
from randovania.network_common import error


@pytest.mark.parametrize("exception", [
    None, error.NotAuthorizedForAction(), error.UserNotAuthorized(),
    error.ServerError(), error.NotLoggedIn(), error.RequestTimeout("timeout"),
    error.InvalidAction("not this"),
    error.UnsupportedClient("Not nice<br />An Error"),
    UnableToConnect("No connect"),
])
async def test_handle_network_errors(skip_qtbot, mocker: MockerFixture, exception):
    mock_warning = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)

    root = QtWidgets.QWidget()
    skip_qtbot.add_widget(root)

    api = MagicMock()
    api.widget_root = root

    fn = AsyncMock(side_effect=exception)
    arg = MagicMock()

    # Run
    wrapped = multiplayer_session_api.handle_network_errors(fn)
    result = await wrapped(api, arg)

    # Assert
    if exception is None:
        assert result == fn.return_value
        mock_warning.assert_not_called()
    else:
        assert result is None
        mock_warning.assert_awaited_once_with(root, ANY, ANY)
