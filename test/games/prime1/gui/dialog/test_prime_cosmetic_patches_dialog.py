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


def test_gunship_follows_power_suit_while_matched(skip_qtbot: pytestqt.qtbot.QtBot, options: Options) -> None:
    cosmetic_patches = PrimeCosmeticPatches(suit_color_rotations=(10, 20, 30, 40))

    dialog = PrimeCosmeticPatchesDialog(None, cosmetic_patches, options)
    skip_qtbot.addWidget(dialog)

    assert dialog.match_gunship_to_power_suit_check.isChecked()
    assert dialog.gunship_rotation_slider.value() == 10

    dialog.power_suit_rotation_slider.setValue(90)
    assert dialog.gunship_rotation_slider.value() == 90
    assert dialog.cosmetic_patches.active_gunship_color_rotation is None

    dialog.gunship_rotation_slider.setValue(45)
    assert dialog.power_suit_rotation_slider.value() == 45
    assert dialog.cosmetic_patches.suit_color_rotations == (45, 20, 30, 40)
    assert dialog.cosmetic_patches.active_gunship_color_rotation is None

    dialog.match_gunship_to_power_suit_check.setChecked(False)
    assert dialog.cosmetic_patches.active_gunship_color_rotation == 45

    dialog.gunship_rotation_slider.setValue(180)
    assert dialog.cosmetic_patches.active_gunship_color_rotation == 180
    assert dialog.cosmetic_patches.suit_color_rotations == (45, 20, 30, 40)


def test_fusion_forces_gunship_to_not_match(skip_qtbot: pytestqt.qtbot.QtBot, options: Options) -> None:
    cosmetic_patches = PrimeCosmeticPatches(gunship_color_rotation=180)

    dialog = PrimeCosmeticPatchesDialog(None, cosmetic_patches, options)
    skip_qtbot.addWidget(dialog)

    assert dialog.match_gunship_to_power_suit_check.isEnabled()
    assert dialog.match_gunship_to_power_suit_check.isChecked()

    dialog.force_fusion_check.setChecked(True)
    assert not dialog.match_gunship_to_power_suit_check.isChecked()
    assert not dialog.match_gunship_to_power_suit_check.isEnabled()
    assert dialog.gunship_rotation_slider.isEnabled()
    assert dialog.gunship_rotation_slider.value() == 180
    assert dialog.cosmetic_patches.active_gunship_color_rotation == 180

    dialog.force_fusion_check.setChecked(False)
    assert dialog.cosmetic_patches == cosmetic_patches


def test_custom_hud_color(skip_qtbot: pytestqt.qtbot.QtBot, options: Options) -> None:
    cosmetic_patches = PrimeCosmeticPatches(use_hud_color=False)

    dialog = PrimeCosmeticPatchesDialog(None, cosmetic_patches, options)
    skip_qtbot.addWidget(dialog)

    skip_qtbot.mouseClick(dialog.custom_hud_color, QtCore.Qt.MouseButton.LeftButton)

    assert dialog.cosmetic_patches == PrimeCosmeticPatches(use_hud_color=True)
