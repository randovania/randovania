from __future__ import annotations

import traceback
import typing

from PySide6 import QtWidgets

from randovania.games.prime2.patcher.claris_randomizer import ClarisRandomizerExportError


def create_box_for_exception(val: BaseException) -> QtWidgets.QMessageBox:
    box = QtWidgets.QMessageBox(
        QtWidgets.QMessageBox.Icon.Critical,
        "An exception was raised",
        (
            f"An unhandled Exception occurred:\n{val}\n\n"
            "When reporting, make sure to paste the entire contents of the following box."
            "\nIt has already been copied to your clipboard."
        ),
        QtWidgets.QMessageBox.StandardButton.Ok,
    )
    from randovania.gui.lib import common_qt_lib

    common_qt_lib.set_default_window_icon(box)

    detailed_exception = "".join(traceback.format_exception(val))
    if isinstance(val, ClarisRandomizerExportError):
        detailed_exception += "\n\n"
        detailed_exception += val.detailed_text()

    box.setDetailedText(detailed_exception)

    common_qt_lib.set_clipboard(detailed_exception)

    # Expand the detailed text
    for button in box.buttons():
        if box.buttonRole(button) == QtWidgets.QMessageBox.ButtonRole.ActionRole:
            button.click()
            break

    box_layout = typing.cast("QtWidgets.QGridLayout", box.layout())
    box_layout.addItem(
        QtWidgets.QSpacerItem(600, 0, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding),
        box_layout.rowCount(),
        0,
        1,
        box_layout.columnCount(),
    )
    return box
