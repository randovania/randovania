from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtWidgets

import randovania
from randovania.gui.generated.reporting_optout_widget_ui import Ui_ReportingOptOutWidget
from randovania.gui.lib import common_qt_lib, signal_handling

if TYPE_CHECKING:
    from randovania.interface_common.options import Options


class ReportingOptOutWidget(QtWidgets.QWidget, Ui_ReportingOptOutWidget):
    options: Options

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)

        if randovania.is_dev_version():
            self.intro_label.setText(
                self.intro_label.text() + "\n\nTo help with the beta testing process, "
                "these settings are always enabled in dev builds."
            )
            self.allow_reports_check.setEnabled(False)
            self.include_user_check.setEnabled(False)
        else:
            signal_handling.on_checked(self.allow_reports_check, self._on_allow_reports)
            signal_handling.on_checked(self.include_user_check, self._on_include_user)

    def on_options_changed(self, options: Options):
        self.options = options
        self.allow_reports_check.setChecked(options.allow_crash_reporting or randovania.is_dev_version())
        self.include_user_check.setChecked(options.use_user_for_crash_reporting or randovania.is_dev_version())

    def _on_allow_reports(self, value: bool):
        with self.options as opt:
            opt.allow_crash_reporting = value

    def _on_include_user(self, value: bool):
        with self.options as opt:
            opt.use_user_for_crash_reporting = value
