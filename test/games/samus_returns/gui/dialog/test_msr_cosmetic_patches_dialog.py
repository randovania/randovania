from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from PySide6 import QtCore

from randovania.games.samus_returns.gui.dialog.cosmetic_patches_dialog import MSRCosmeticPatchesDialog
from randovania.games.samus_returns.layout.msr_cosmetic_patches import MSRCosmeticPatches, MSRRoomGuiType
from randovania.gui.lib.signal_handling import set_combo_with_value

if TYPE_CHECKING:
    import pytestqt.qtbot  # type: ignore[import]


def test_custom_laser_color(skip_qtbot: pytestqt.qtbot.QtBot) -> None:
    cosmetic_patches = MSRCosmeticPatches(use_laser_color=False)

    dialog = MSRCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    skip_qtbot.mouseClick(dialog.custom_laser_color_check, QtCore.Qt.MouseButton.LeftButton)

    assert dialog.cosmetic_patches == MSRCosmeticPatches(use_laser_color=True)


def test_custom_energy_tank_color(skip_qtbot: pytestqt.qtbot.QtBot) -> None:
    cosmetic_patches = MSRCosmeticPatches(use_energy_tank_color=False)

    dialog = MSRCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    skip_qtbot.mouseClick(dialog.custom_energy_tank_color_check, QtCore.Qt.MouseButton.LeftButton)

    assert dialog.cosmetic_patches == MSRCosmeticPatches(use_energy_tank_color=True)


def test_custom_aeion_bar_color(skip_qtbot: pytestqt.qtbot.QtBot) -> None:
    cosmetic_patches = MSRCosmeticPatches(use_aeion_bar_color=False)

    dialog = MSRCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    skip_qtbot.mouseClick(dialog.custom_aeion_bar_color_check, QtCore.Qt.MouseButton.LeftButton)

    assert dialog.cosmetic_patches == MSRCosmeticPatches(use_aeion_bar_color=True)


def test_custom_ammo_hud_color(skip_qtbot: pytestqt.qtbot.QtBot) -> None:
    cosmetic_patches = MSRCosmeticPatches(use_ammo_hud_color=False)

    dialog = MSRCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    skip_qtbot.mouseClick(dialog.custom_ammo_hud_color_check, QtCore.Qt.MouseButton.LeftButton)

    assert dialog.cosmetic_patches == MSRCosmeticPatches(use_ammo_hud_color=True)


def test_room_names_dropdown(skip_qtbot: pytestqt.qtbot.QtBot) -> None:
    cosmetic_patches = MSRCosmeticPatches(show_room_names=MSRRoomGuiType.NONE)

    dialog = MSRCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    set_combo_with_value(dialog.room_names_dropdown, MSRRoomGuiType.ALWAYS)

    assert dialog.cosmetic_patches == MSRCosmeticPatches(show_room_names=MSRRoomGuiType.ALWAYS)


@pytest.mark.parametrize(
    ("widget_field", "field_name"),
    [
        ("enable_remote_lua", "enable_remote_lua"),
    ],
)
def test_certain_field(skip_qtbot: pytestqt.qtbot.QtBot, widget_field: str, field_name: str) -> None:
    cosmetic_patches = MSRCosmeticPatches(**{field_name: False})  # type: ignore[arg-type]

    dialog = MSRCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    skip_qtbot.mouseClick(getattr(dialog, widget_field), QtCore.Qt.MouseButton.LeftButton)

    assert dialog.cosmetic_patches == MSRCosmeticPatches(**{field_name: True})  # type: ignore[arg-type]
