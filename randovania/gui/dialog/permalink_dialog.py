from PySide2.QtWidgets import QDialog, QApplication

from randovania.gui.generated.permalink_dialog_ui import Ui_PermalinkDialog
from randovania.gui.lib import common_qt_lib
from randovania.layout.permalink import Permalink


class PermalinkDialog(QDialog, Ui_PermalinkDialog):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)

        self.accept_button.setEnabled(False)
        self.accept_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.paste_button.clicked.connect(self._on_paste_button)

        self.permalink_edit.textChanged.connect(self._on_permalink_changed)
        self.permalink_edit.setFocus()

        self._on_paste_button()

    # Permalink
    def get_permalink_from_field(self) -> Permalink:
        return Permalink.from_str(self.permalink_edit.text())

    def _on_permalink_changed(self, value: str):
        common_qt_lib.set_error_border_stylesheet(self.permalink_edit, False)
        common_qt_lib.set_edit_if_different(self.permalink_edit, self.permalink_edit.text().strip())
        self.accept_button.setEnabled(False)
        self.import_error_label.setText("")

        try:
            # Ignoring return value: we only want to know if it's valid
            new_permalink = self.get_permalink_from_field()
            if new_permalink.as_base64_str != self.permalink_edit.text():
                raise ValueError("Imported permalink is different from text field.")
            self.accept_button.setEnabled(True)
        except ValueError as e:
            self.import_error_label.setText(f"Invalid permalink: {e}")
            common_qt_lib.set_error_border_stylesheet(self.permalink_edit, True)

    def _on_paste_button(self):
        self.permalink_edit.setText(QApplication.clipboard().text())
