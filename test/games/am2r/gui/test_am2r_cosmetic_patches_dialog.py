from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from PySide6 import QtCore

from randovania.games.am2r.gui.dialog.cosmetic_patches_dialog import (
    AM2RCosmeticPatchesDialog,
    hue_rotate_color,
)
from randovania.games.am2r.layout.am2r_cosmetic_patches import AM2RCosmeticPatches, MusicMode

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


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
    skip_qtbot: QtBot, music_start_value: MusicMode, option_to_click: str, music_end_value: MusicMode
) -> None:
    cosmetic_patches = AM2RCosmeticPatches(music=music_start_value)

    dialog = AM2RCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)
    str_to_option_map = {
        "vanilla_music_option": dialog.vanilla_music_option,
        "type_music_option": dialog.type_music_option,
        "full_music_option": dialog.full_music_option,
    }
    radio_button = str_to_option_map[option_to_click]

    skip_qtbot.mouseClick(radio_button, QtCore.Qt.MouseButton.LeftButton)

    assert dialog.cosmetic_patches == AM2RCosmeticPatches(music=music_end_value)


def test_show_unexplored_map(skip_qtbot):
    cosmetic_patches = AM2RCosmeticPatches(show_unexplored_map=True)

    dialog = AM2RCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    skip_qtbot.mouseClick(dialog.show_unexplored_map_check, QtCore.Qt.MouseButton.LeftButton)

    assert dialog.cosmetic_patches == AM2RCosmeticPatches(show_unexplored_map=False)


def test_unveiled_blocks(skip_qtbot):
    cosmetic_patches = AM2RCosmeticPatches(unveiled_blocks=True)

    dialog = AM2RCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    skip_qtbot.mouseClick(dialog.unveiled_blocks_check, QtCore.Qt.MouseButton.LeftButton)

    assert dialog.cosmetic_patches == AM2RCosmeticPatches(unveiled_blocks=False)


def test_custom_hud_colors(skip_qtbot):
    # Setup
    cosmetic_patches = AM2RCosmeticPatches(health_hud_rotation=0, etank_hud_rotation=0, dna_hud_rotation=0)

    dialog = AM2RCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    assert dialog.custom_health_rotation_square.styleSheet() == "background-color: rgb(255,221,0)"
    assert dialog.custom_etank_rotation_square.styleSheet() == "background-color: rgb(112,222,250)"
    assert dialog.custom_dna_rotation_square.styleSheet() == "background-color: rgb(49,208,5)"

    # Run
    for field in [
        dialog.custom_health_rotation_field,
        dialog.custom_etank_rotation_field,
        dialog.custom_dna_rotation_field,
    ]:
        field.setValue(50)

    # Assert
    assert dialog.cosmetic_patches == AM2RCosmeticPatches(
        health_hud_rotation=50, etank_hud_rotation=50, dna_hud_rotation=50
    )
    assert dialog.custom_health_rotation_square.styleSheet() == "background-color: rgb(76,255,0)"
    assert dialog.custom_etank_rotation_square.styleSheet() == "background-color: rgb(116,112,250)"
    assert dialog.custom_dna_rotation_square.styleSheet() == "background-color: rgb(5,208,130)"


def test_hue_rotate_color():
    initial_color = (240, 128, 97)
    color = hue_rotate_color(initial_color, 360)
    assert color == initial_color

    color_2 = hue_rotate_color(initial_color, 380)
    color_3 = hue_rotate_color(initial_color, 20)
    assert color_2 == color_3

    color_4 = hue_rotate_color(initial_color, 0)
    assert color_4 == initial_color
