from pathlib import Path
from typing import Optional

from PySide2 import QtWidgets

from randovania.gui.lib import async_dialog


async def _prompt_user_for_file(
        parent: QtWidgets.QWidget,
        caption: str,
        file_filter: str,
        current_dir: Optional[str] = None,
        new_file: bool = False,
) -> Optional[Path]:
    """
    Helper function for all `prompt_user_for_*` functions.
    :param parent:
    :param caption:
    :param file_filter:
    :param new_file: If false, prompt for an existing file.
    :return: A string if the user selected a file, None otherwise
    """

    file_dialog = QtWidgets.QFileDialog(parent, caption, current_dir or "", file_filter)

    if new_file:
        file_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
    else:
        file_dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)

    result = await async_dialog.execute_dialog(file_dialog)
    if result != QtWidgets.QDialog.Accepted:
        return None

    return Path(file_dialog.selectedFiles()[0])


async def prompt_input_layout(parent: QtWidgets.QWidget) -> Optional[Path]:
    """
    Shows an QFileDialog asking the user for a Randovania LayoutDescription
    :param parent:
    :return: A string if the user selected a file, None otherwise
    """
    from randovania.layout.layout_description import LayoutDescription
    return await _prompt_user_for_file(
        parent, caption="Select a Randovania seed log.",
        file_filter="Randovania Game, *.{}".format(LayoutDescription.file_extension()),
        new_file=False,
    )
