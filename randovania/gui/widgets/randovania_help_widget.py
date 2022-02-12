from PySide2 import QtWidgets, QtGui

from randovania.gui.generated.randovania_help_widget_ui import Ui_RandovaniaHelpWidget
from randovania.gui.lib import common_qt_lib


class RandovaniaHelpWidget(QtWidgets.QTabWidget, Ui_RandovaniaHelpWidget):
    _first_show: bool = True

    def _on_first_show(self):
        self.setupUi(self)
        common_qt_lib.set_icon_data_paths(self.database_viewer_label)
        common_qt_lib.set_icon_data_paths(self.tracker_label)

    def showEvent(self, arg: QtGui.QShowEvent) -> None:
        if self._first_show:
            self._first_show = False
            self._on_first_show()

        return super().showEvent(arg)
