from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtCore

from randovania.games.prime1.gui.dialog.prime_cosmetic_patches_dialog import (
    PrimeCosmeticPatchesDialog,
)
from randovania.games.prime1.layout.prime_cosmetic_patches import PrimeCosmeticPatches

if TYPE_CHECKING:
    import pytestqt.qtbot


def test_open_map(skip_qtbot: pytestqt.qtbot.QtBot) -> None:
    cosmetic_patches = PrimeCosmeticPatches(open_map=True)

    dialog = PrimeCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    skip_qtbot.mouseClick(dialog.open_map_check, QtCore.Qt.MouseButton.LeftButton)

    assert dialog.cosmetic_patches == PrimeCosmeticPatches(open_map=False)


def test_force_fusion(skip_qtbot: pytestqt.qtbot.QtBot) -> None:
    cosmetic_patches = PrimeCosmeticPatches(force_fusion=True)

    dialog = PrimeCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    skip_qtbot.mouseClick(dialog.force_fusion_check, QtCore.Qt.MouseButton.LeftButton)

    assert dialog.cosmetic_patches == PrimeCosmeticPatches(force_fusion=False)


def test_custom_hud_color(skip_qtbot: pytestqt.qtbot.QtBot) -> None:
    cosmetic_patches = PrimeCosmeticPatches(use_hud_color=False)

    dialog = PrimeCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    skip_qtbot.mouseClick(dialog.custom_hud_color, QtCore.Qt.MouseButton.LeftButton)

    assert dialog.cosmetic_patches == PrimeCosmeticPatches(use_hud_color=True)
