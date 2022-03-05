import asyncio
from typing import Optional

from PySide2 import QtWidgets

from randovania.gui.lib import common_qt_lib


async def cancellable_wait(parent: Optional[QtWidgets.QWidget], task: asyncio.Task,
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
        await task
    finally:
        message_box.close()
