import asyncio

from PySide6 import QtWidgets

from randovania.gui.lib import common_qt_lib


async def cancellable_wait(parent: QtWidgets.QWidget | None, task: asyncio.Task,
                           title: str, message: str):
    message_box = QtWidgets.QMessageBox(
        QtWidgets.QMessageBox.NoIcon, title,
        message,
        QtWidgets.QMessageBox.Cancel,
        parent,
    )
    common_qt_lib.set_default_window_icon(message_box)

    message_box.rejected.connect(task.cancel)
    message_box.show()
    try:
        return await task
    finally:
        message_box.close()
