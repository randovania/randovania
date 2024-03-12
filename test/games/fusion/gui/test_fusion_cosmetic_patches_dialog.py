from __future__ import annotations

import pytest
from PySide6 import QtCore

from randovania.games.fusion.gui.dialog.cosmetic_patches_dialog import FusionCosmeticPatchesDialog
from randovania.games.fusion.layout.fusion_cosmetic_patches import ColorSpace, FusionCosmeticPatches


@pytest.mark.parametrize(
    ("field_name", "widget_field"),
    [
        ("enable_suit_palette", "suit_palette_check"),
        ("enable_beam_palette", "beam_palette_check"),
        ("enable_enemy_palette", "enemy_palette_check"),
        ("enable_tileset_palette", "tileset_palette_check"),
        ("disable_music", "disable_music_check"),
        ("disable_sfx", "disable_sfx_check"),
    ],
)
def test_enable_checkboxes(skip_qtbot, field_name: str, widget_field: str) -> None:
    cosmetic_patches = FusionCosmeticPatches(**{field_name: False})  # type: ignore[arg-type]

    dialog = FusionCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)
    # Run
    skip_qtbot.mouseClick(getattr(dialog, widget_field), QtCore.Qt.MouseButton.LeftButton)
    # Assert
    assert dialog.cosmetic_patches == FusionCosmeticPatches(**{field_name: True})  # type: ignore[arg-type]


def test_color_space(skip_qtbot):
    cosmetic_patches = FusionCosmeticPatches(color_space=ColorSpace.Oklab)

    dialog = FusionCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)
    # Run
    dialog.color_space_combo.setCurrentIndex(1)
    # Assert
    assert dialog.cosmetic_patches == FusionCosmeticPatches(color_space=ColorSpace.HSV)

    # Run
    dialog.color_space_combo.setCurrentIndex(0)
    # Assert
    assert dialog.cosmetic_patches == FusionCosmeticPatches(color_space=ColorSpace.Oklab)


@pytest.mark.parametrize(
    ("music_start_value", "option_to_click", "music_end_value"),
    [
        (False, "stereo_option", True),
        (True, "mono_option", False),
    ],
)
def test_change_music_option(skip_qtbot, music_start_value: bool, option_to_click: str, music_end_value: bool) -> None:
    cosmetic_patches = FusionCosmeticPatches(stereo_default=music_start_value)

    dialog = FusionCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    radio_button = getattr(dialog, option_to_click)
    skip_qtbot.mouseClick(radio_button, QtCore.Qt.MouseButton.LeftButton)

    assert dialog.cosmetic_patches == FusionCosmeticPatches(stereo_default=music_end_value)
