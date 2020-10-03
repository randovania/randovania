from PySide2 import QtWidgets

from randovania.interface_common.options import Options, DecodeFailedException


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
