from PySide2 import QtCore

from randovania.games.prime1.gui.dialog.prime_cosmetic_patches_dialog import PrimeCosmeticPatchesDialog
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
