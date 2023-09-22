from __future__ import annotations

import logging

from PySide6 import QtWidgets

from randovania.gui.lib import async_dialog
from randovania.interface_common.options import DecodeFailedException, Options


async def load_options_from_disk(options: Options) -> bool:
    try:
        options.load_from_disk()
        return True

    except DecodeFailedException as decode_failed:
        user_response = await async_dialog.message_box(
            None,
            QtWidgets.QMessageBox.Icon.Critical,
            "Error loading previous settings",
            (
                "The following error occurred while restoring your settings:\n"
                f"{decode_failed}\n\n"
                "Do you want to reset this part of your settings?"
            ),
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        )
        if user_response == QtWidgets.QMessageBox.StandardButton.Yes:
            options.load_from_disk(True)
            return True
        else:
            logging.exception("")
            return False
