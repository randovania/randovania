from PySide2 import QtCore

from randovania.games.prime1.gui.dialog.prime_cosmetic_patches_dialog import PrimeCosmeticPatchesDialog, \
    hue_rotate_color
from randovania.games.prime1.layout.prime_cosmetic_patches import PrimeCosmeticPatches


def test_qol_cosmetic(skip_qtbot):
    cosmetic_patches = PrimeCosmeticPatches(qol_cosmetic=False)

    dialog = PrimeCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    skip_qtbot.mouseClick(dialog.qol_cosmetic_check, QtCore.Qt.LeftButton)

    assert dialog.cosmetic_patches == PrimeCosmeticPatches(qol_cosmetic=True)


def test_open_map(skip_qtbot):
    cosmetic_patches = PrimeCosmeticPatches(open_map=True)

    dialog = PrimeCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    skip_qtbot.mouseClick(dialog.open_map_check, QtCore.Qt.LeftButton)

    assert dialog.cosmetic_patches == PrimeCosmeticPatches(open_map=False)


def test_custom_hud_color(skip_qtbot):
    cosmetic_patches = PrimeCosmeticPatches(use_hud_color=False)

    dialog = PrimeCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    skip_qtbot.mouseClick(dialog.custom_hud_color, QtCore.Qt.LeftButton)

    assert dialog.cosmetic_patches == PrimeCosmeticPatches(use_hud_color=True)


def test_hue_rotate_color():
    initial_color = (240, 128, 97)
    color = hue_rotate_color(initial_color, 360)
    assert color == initial_color

    color_2 = hue_rotate_color(initial_color, 380)
    color_3 = hue_rotate_color(initial_color, 20)
    assert color_2 == color_3

    color_4 = hue_rotate_color(initial_color, 0)
    assert color_4 == initial_color
