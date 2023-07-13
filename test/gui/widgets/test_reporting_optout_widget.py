from __future__ import annotations

from unittest.mock import MagicMock

from PySide6.QtGui import Qt

from randovania.gui.widgets.reporting_optout_widget import ReportingOptOutWidget


def test_on_options_changed(skip_qtbot, is_dev_version):
    options = MagicMock()
    options.allow_crash_reporting = False
    options.use_user_for_crash_reporting = False

    widget = ReportingOptOutWidget()
    skip_qtbot.addWidget(widget)

    widget.on_options_changed(options)
    assert widget.allow_reports_check.isChecked() is is_dev_version
    assert widget.include_user_check.isChecked() is is_dev_version

    skip_qtbot.mouseClick(widget.allow_reports_check, Qt.MouseButton.LeftButton)
    skip_qtbot.mouseClick(widget.include_user_check, Qt.MouseButton.LeftButton)
    if is_dev_version:
        assert not widget.allow_reports_check.isEnabled()
        assert not widget.include_user_check.isEnabled()
        options.__enter__.assert_not_called()
    else:
        assert options.__enter__.return_value.allow_crash_reporting is True
        assert options.__enter__.return_value.use_user_for_crash_reporting is True
