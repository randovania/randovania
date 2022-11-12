from unittest.mock import MagicMock, AsyncMock

import pytest
from PySide6 import QtWidgets

from randovania.gui.lib import async_dialog


@pytest.mark.parametrize("status", [QtWidgets.QDialog.DialogCode.Rejected, QtWidgets.QDialog.DialogCode.Accepted])
async def test_execute_execute_dialog(skip_qtbot, status):
    class CustomDialog(QtWidgets.QDialog):
        def show(self):
            self.done(status)
            # super().show()

    diag = CustomDialog()
    result = await async_dialog.execute_dialog(diag)
    assert result == status


async def test_warning(skip_qtbot, mocker):
    root = MagicMock()
    mock_message_box: AsyncMock = mocker.patch("randovania.gui.lib.async_dialog.message_box")

    # Run
    result = await async_dialog.warning(root, "MyTitle", "TheBody",
                                        async_dialog.StandardButton.Yes, async_dialog.StandardButton.Yes)

    # Assert
    mock_message_box.assert_awaited_once_with(
        root, QtWidgets.QMessageBox.Icon.Warning, "MyTitle", "TheBody",
        async_dialog.StandardButton.Yes, async_dialog.StandardButton.Yes
    )
    assert result == mock_message_box.return_value
