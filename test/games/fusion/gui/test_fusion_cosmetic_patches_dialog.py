from __future__ import annotations

from PySide6 import QtCore

from randovania.games.fusion.gui.dialog.cosmetic_patches_dialog import FusionCosmeticPatchesDialog
from randovania.games.fusion.layout.fusion_cosmetic_patches import ColorSpace, FusionCosmeticPatches


def test_suit_palette(skip_qtbot):
    cosmetic_patches = FusionCosmeticPatches(enable_suit_palette=False)

    dialog = FusionCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    skip_qtbot.mouseClick(dialog.suit_palette_check, QtCore.Qt.MouseButton.LeftButton)

    assert dialog.cosmetic_patches == FusionCosmeticPatches(enable_suit_palette=True)


def test_beam_palette(skip_qtbot):
    cosmetic_patches = FusionCosmeticPatches(enable_beam_palette=False)

    dialog = FusionCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    skip_qtbot.mouseClick(dialog.beam_palette_check, QtCore.Qt.MouseButton.LeftButton)

    assert dialog.cosmetic_patches == FusionCosmeticPatches(enable_beam_palette=True)


def test_enemy_palette(skip_qtbot):
    cosmetic_patches = FusionCosmeticPatches(enable_enemy_palette=False)

    dialog = FusionCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    skip_qtbot.mouseClick(dialog.enemy_palette_check, QtCore.Qt.MouseButton.LeftButton)

    assert dialog.cosmetic_patches == FusionCosmeticPatches(enable_enemy_palette=True)


def test_tileset_palette(skip_qtbot):
    cosmetic_patches = FusionCosmeticPatches(enable_tileset_palette=False)

    dialog = FusionCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    skip_qtbot.mouseClick(dialog.tileset_palette_check, QtCore.Qt.MouseButton.LeftButton)

    assert dialog.cosmetic_patches == FusionCosmeticPatches(enable_tileset_palette=True)


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
