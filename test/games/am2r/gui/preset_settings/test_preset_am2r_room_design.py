from __future__ import annotations

import dataclasses
import uuid
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from PySide6 import QtCore, QtWidgets

from randovania.games.am2r.gui.preset_settings.am2r_room_design_tab import PresetAM2RRoomDesign
from randovania.games.am2r.layout.am2r_configuration import AM2RConfiguration
from randovania.interface_common.preset_editor import PresetEditor

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot

    from randovania.game_description.game_description import GameDescription
    from randovania.interface_common.preset_manager import PresetManager


def test_flip_checks(skip_qtbot: QtBot, am2r_game_description: GameDescription, preset_manager: PresetManager) -> None:
    game = am2r_game_description.game
    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("b41fde84-1f57-4b79-8cd6-3e5a78077fa6"))
    base_configuration = preset.configuration
    options = MagicMock()
    assert isinstance(base_configuration, AM2RConfiguration)

    tab = PresetAM2RRoomDesign(PresetEditor(preset, options), am2r_game_description, MagicMock())
    skip_qtbot.addWidget(tab)
    tab.on_preset_changed(preset)

    for widget in tab.findChildren(QtWidgets.QCheckBox):
        assert isinstance(widget, QtWidgets.QCheckBox)
        name = widget.objectName()[:-6]  # attribute name minus the "_check" in the name
        assert name in tab._CHECKBOX_FIELDS
        before = widget.isChecked()
        assert getattr(tab._editor.configuration, name) == before
        skip_qtbot.mouseClick(widget, QtCore.Qt.MouseButton.LeftButton)
        after = widget.isChecked()

        # Assert that the value changed
        assert before != after
        assert getattr(tab._editor.configuration, name) == after
