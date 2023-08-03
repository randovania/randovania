from __future__ import annotations

from PySide6 import QtCore

from randovania.games.prime2.gui.dialog.echoes_cosmetic_patches_dialog import EchoesCosmeticPatchesDialog
from randovania.games.prime2.layout.echoes_cosmetic_patches import EchoesCosmeticPatches


def test_suit_cosmetics(skip_qtbot):
    cosmetic_patches = EchoesCosmeticPatches()

    dialog = EchoesCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    def click(target):
        skip_qtbot.mouseClick(target, QtCore.Qt.MouseButton.LeftButton)

    click(dialog.suits_foldable)

    # Simple suits
    click(dialog.simple_left_button)
    click(dialog.simple_right_button)

    # Separate suits
    click(dialog.advanced_check)
    click(dialog.varia_left_button)
    click(dialog.varia_right_button)
    click(dialog.dark_left_button)
    click(dialog.dark_right_button)
    click(dialog.light_left_button)
    click(dialog.light_right_button)
    click(dialog.advanced_check)

    assert dialog.cosmetic_patches == EchoesCosmeticPatches()
