from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtCore

from randovania.games.prime1.gui.dialog.prime_cosmetic_patches_dialog import (
    PrimeCosmeticPatchesDialog,
)
from randovania.games.prime1.layout.prime_cosmetic_patches import PrimeCosmeticPatches

if TYPE_CHECKING:
    import pytestqt.qtbot

    from randovania.interface_common.options import Options


def test_open_map(skip_qtbot: pytestqt.qtbot.QtBot, options: Options) -> None:
    cosmetic_patches = PrimeCosmeticPatches(open_map=True)

    dialog = PrimeCosmeticPatchesDialog(None, cosmetic_patches, options)
    skip_qtbot.addWidget(dialog)

    skip_qtbot.mouseClick(dialog.open_map_check, QtCore.Qt.MouseButton.LeftButton)

    assert dialog.cosmetic_patches == PrimeCosmeticPatches(open_map=False)


def test_force_fusion(skip_qtbot: pytestqt.qtbot.QtBot, options: Options) -> None:
    cosmetic_patches = PrimeCosmeticPatches(force_fusion=True)

    dialog = PrimeCosmeticPatchesDialog(None, cosmetic_patches, options)
    skip_qtbot.addWidget(dialog)

    skip_qtbot.mouseClick(dialog.force_fusion_check, QtCore.Qt.MouseButton.LeftButton)

    assert dialog.cosmetic_patches == PrimeCosmeticPatches(force_fusion=False)


def test_rainbow_phazon_ball(skip_qtbot: pytestqt.qtbot.QtBot, options: Options) -> None:
    cosmetic_patches = PrimeCosmeticPatches(rainbow_phazon_ball=False)

    dialog = PrimeCosmeticPatchesDialog(None, cosmetic_patches, options)
    skip_qtbot.addWidget(dialog)

    skip_qtbot.mouseClick(dialog.rainbow_phazon_ball_check, QtCore.Qt.MouseButton.LeftButton)

    assert dialog.cosmetic_patches == PrimeCosmeticPatches(rainbow_phazon_ball=True)


def test_suit_rotations_are_remembered_per_fusion_state(skip_qtbot: pytestqt.qtbot.QtBot, options: Options) -> None:
    cosmetic_patches = PrimeCosmeticPatches(
        suit_color_rotations=(10, 20, 30, 40),
        fusion_suit_color_rotations=(50, 60, 70, 80),
    )

    dialog = PrimeCosmeticPatchesDialog(None, cosmetic_patches, options)
    skip_qtbot.addWidget(dialog)

    assert [slider.value() for slider in dialog.suit_rotation_sliders] == [10, 20, 30, 40]

    dialog.force_fusion_check.setChecked(True)
    assert [slider.value() for slider in dialog.suit_rotation_sliders] == [50, 60, 70, 80]

    dialog.power_suit_rotation_slider.setValue(90)
    dialog.force_fusion_check.setChecked(False)

    assert [slider.value() for slider in dialog.suit_rotation_sliders] == [10, 20, 30, 40]
    assert dialog.cosmetic_patches == PrimeCosmeticPatches(
        suit_color_rotations=(10, 20, 30, 40),
        fusion_suit_color_rotations=(90, 60, 70, 80),
    )


def test_custom_hud_color(skip_qtbot: pytestqt.qtbot.QtBot, options: Options) -> None:
    cosmetic_patches = PrimeCosmeticPatches(use_hud_color=False)

    dialog = PrimeCosmeticPatchesDialog(None, cosmetic_patches, options)
    skip_qtbot.addWidget(dialog)

    skip_qtbot.mouseClick(dialog.custom_hud_color, QtCore.Qt.MouseButton.LeftButton)

    assert dialog.cosmetic_patches == PrimeCosmeticPatches(use_hud_color=True)
