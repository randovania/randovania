import asyncio
from typing import Optional

from PySide2 import QtWidgets

from randovania.gui.lib import common_qt_lib


async def execute_dialog(dialog: QtWidgets.QDialog) -> QtWidgets.QDialog.DialogCode:
    """
    An async version of dialog.exec_, internally using QDialog.show
    :param dialog:
    :return:
    """
    future = asyncio.get_event_loop().create_future()

    dialog.finished.connect(future.set_result)
    try:
        dialog.show()
        return await future
    finally:
        dialog.finished.disconnect(future.set_result)


async def message_box(parent: Optional[QtWidgets.QWidget],
                      icon: QtWidgets.QMessageBox.Icon,
                      title: str, text: str,
                      buttons: QtWidgets.QMessageBox.StandardButtons = QtWidgets.QMessageBox.Ok,
                      default_button: QtWidgets.QMessageBox.StandardButton = QtWidgets.QMessageBox.NoButton,
                      ) -> QtWidgets.QMessageBox.StandardButton:
    box = QtWidgets.QMessageBox(icon, title, text, buttons, parent)
    box.setDefaultButton(default_button)
    common_qt_lib.set_default_window_icon(box)
    return await execute_dialog(box)


async def warning(parent: Optional[QtWidgets.QWidget],
                  title: str, text: str,
                  buttons: QtWidgets.QMessageBox.StandardButtons = QtWidgets.QMessageBox.Ok,
                  default_button: QtWidgets.QMessageBox.StandardButton = QtWidgets.QMessageBox.NoButton,
                  ) -> QtWidgets.QMessageBox.StandardButton:
    return await message_box(parent, QtWidgets.QMessageBox.Warning, title, text, buttons, default_button)
