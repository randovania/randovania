from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from PySide6 import QtCore

from randovania.games.samus_returns.gui.dialog.cosmetic_patches_dialog import MSRCosmeticPatchesDialog
from randovania.games.samus_returns.layout.msr_cosmetic_patches import MSRCosmeticPatches, MSRRoomGuiType, MusicMode
from randovania.gui.lib.signal_handling import set_combo_with_value

if TYPE_CHECKING:
    import pytestqt.qtbot


@pytest.mark.parametrize(
    ("music_start_value", "option_to_click", "music_end_value"),
    [
        (MusicMode.VANILLA, "vanilla_music_option", MusicMode.VANILLA),
        (MusicMode.VANILLA, "type_music_option", MusicMode.TYPE),
        (MusicMode.VANILLA, "full_music_option", MusicMode.FULL),
        (MusicMode.TYPE, "vanilla_music_option", MusicMode.VANILLA),
        (MusicMode.TYPE, "type_music_option", MusicMode.TYPE),
        (MusicMode.TYPE, "full_music_option", MusicMode.FULL),
        (MusicMode.FULL, "vanilla_music_option", MusicMode.VANILLA),
        (MusicMode.FULL, "type_music_option", MusicMode.TYPE),
        (MusicMode.FULL, "full_music_option", MusicMode.FULL),
    ],
)
def test_change_music_option(
    skip_qtbot: pytestqt.qtbot.QtBot, music_start_value: MusicMode, option_to_click: str, music_end_value: MusicMode
) -> None:
    cosmetic_patches = MSRCosmeticPatches(music=music_start_value)

    dialog = MSRCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)
    str_to_option_map = {
        "vanilla_music_option": dialog.vanilla_music_option,
        "type_music_option": dialog.type_music_option,
        "full_music_option": dialog.full_music_option,
    }
    radio_button = str_to_option_map[option_to_click]

    skip_qtbot.mouseClick(radio_button, QtCore.Qt.MouseButton.LeftButton)

    assert dialog.cosmetic_patches == MSRCosmeticPatches(music=music_end_value)


@pytest.mark.parametrize(
    ("slider_name", "label_name", "field_name"),
    [
        ("music_slider", "music_label", "music_volume"),
        ("ambience_slider", "ambience_label", "ambience_volume"),
    ],
)
def test_certain_slider(skip_qtbot: pytestqt.qtbot.QtBot, slider_name: str, label_name: str, field_name: str) -> None:
    cosmetic_patches = MSRCosmeticPatches(**{field_name: 0})  # type: ignore[arg-type]

    dialog = MSRCosmeticPatchesDialog(None, cosmetic_patches)
    label = getattr(dialog, label_name)
    skip_qtbot.addWidget(dialog)
    assert label.text() == "  0%"

    slider = getattr(dialog, slider_name)
    slider.setValue(80)

    assert dialog.cosmetic_patches == MSRCosmeticPatches(**{field_name: 80})  # type: ignore[arg-type]
    assert label.text() == " 80%"
    assert slider.value() == 80


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
