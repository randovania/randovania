from __future__ import annotations

from typing import TYPE_CHECKING

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


def test_custom_grapple_laser_color(skip_qtbot: pytestqt.qtbot.QtBot) -> None:
    cosmetic_patches = MSRCosmeticPatches(use_grapple_laser_color=False)

    dialog = MSRCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    skip_qtbot.mouseClick(dialog.custom_grapple_laser_color_check, QtCore.Qt.MouseButton.LeftButton)

    assert dialog.cosmetic_patches == MSRCosmeticPatches(use_grapple_laser_color=True)


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
