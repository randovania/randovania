from PySide2 import QtWidgets

from randovania.gui.generated.scroll_label_dialog_ui import Ui_ScrollLabelDialog
from randovania.gui.lib import common_qt_lib


class ScrollLabelDialog(QtWidgets.QDialog, Ui_ScrollLabelDialog):
    def __init__(self, text: str, title: str, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)
        self.setWindowTitle(title)
        self.label.setText(text)

        self.button_box.accepted.connect(self.accept)
