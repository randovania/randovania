import logging
import os

from PySide2 import QtWidgets

from randovania.interface_common.options import Options, DecodeFailedException
from randovania.interface_common.preset_manager import PresetManager, InvalidPreset


def load_options_from_disk(options: Options) -> bool:
    parent: QtWidgets.QWidget = None
    try:
        options.load_from_disk()
        return True

    except DecodeFailedException as decode_failed:
        user_response = QtWidgets.QMessageBox.critical(
            parent,
            "Error loading previous settings",
            ("The following error occurred while restoring your settings:\n"
             "{}\n\n"
             "Do you want to reset this part of your settings?").format(decode_failed),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        if user_response == QtWidgets.QMessageBox.Yes:
            options.load_from_disk(True)
            return True
        else:
            return False


def load_user_presets(preset_manager: PresetManager) -> bool:
    parent: QtWidgets.QWidget = None
    try:
        preset_manager.load_user_presets(False)
        return True

    except InvalidPreset as invalid_file:
        user_response = QtWidgets.QMessageBox.critical(
            parent,
            "Error loading saved preset",
            ("An error happened when loading the preset '{}'.\n\n"
             "Do you want to delete this preset? Say No to ignore all invalid presets in this session."
             ).format(invalid_file.file.stem),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel,
            QtWidgets.QMessageBox.No
        )
        if user_response == QtWidgets.QMessageBox.Yes:
            os.remove(invalid_file.file)
            return load_user_presets(preset_manager)

        logging.error(f"Error loading preset {invalid_file.file}", exc_info=invalid_file.original_exception)
        if user_response == QtWidgets.QMessageBox.No:
            preset_manager.load_user_presets(True)
            return True
        else:
            return False
