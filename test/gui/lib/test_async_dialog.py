import pytest
from PySide2 import QtWidgets

from randovania.gui.lib import async_dialog


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [QtWidgets.QDialog.Rejected, QtWidgets.QDialog.Accepted])
async def test_execute_execute_dialog(skip_qtbot, status):
    class CustomDialog(QtWidgets.QDialog):
        def show(self):
            self.done(status)
            # super().show()

    diag = CustomDialog()
    result = await async_dialog.execute_dialog(diag)
    assert result == status
