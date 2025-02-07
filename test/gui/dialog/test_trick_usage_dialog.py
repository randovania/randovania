from __future__ import annotations

from unittest.mock import MagicMock

from PySide6.QtWidgets import QWidget

from randovania.gui.dialog import trick_usage_popup


def test_create(skip_qtbot, default_echoes_preset):
    # Setup
    main_window = QWidget()
    main_window.open_data_visualizer_at = MagicMock()
    skip_qtbot.add_widget(main_window)

    # Run
    popup = trick_usage_popup.TrickUsagePopup(main_window, main_window, default_echoes_preset)

    # Assert
    assert popup.area_list_label.text() == ""
