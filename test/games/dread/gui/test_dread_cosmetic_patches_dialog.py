from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from PySide6 import QtCore

from randovania.games.dread.gui.dialog.dread_cosmetic_patches_dialog import DreadCosmeticPatchesDialog
from randovania.games.dread.layout.dread_cosmetic_patches import (
    DreadCosmeticPatches,
    DreadMissileCosmeticType,
    DreadRoomGuiType,
    DreadShieldType,
)
from randovania.gui.lib.signal_handling import set_combo_with_value

if TYPE_CHECKING:
    import pytestqt.qtbot  # type: ignore[import]


@pytest.mark.parametrize(
    ("widget_field", "field_name"),
    [
        ("show_boss_life", "show_boss_lifebar"),
        ("show_enemy_life", "show_enemy_life"),
        ("show_enemy_damage", "show_enemy_damage"),
        ("show_player_damage", "show_player_damage"),
        ("show_death_counter", "show_death_counter"),
        ("enable_auto_tracker", "enable_auto_tracker"),
    ],
)
def test_certain_field(skip_qtbot: pytestqt.qtbot.QtBot, widget_field: str, field_name: str) -> None:
    cosmetic_patches = DreadCosmeticPatches(**{field_name: False})  # type: ignore[arg-type]

    dialog = DreadCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    skip_qtbot.mouseClick(getattr(dialog, widget_field), QtCore.Qt.MouseButton.LeftButton)

    assert dialog.cosmetic_patches == DreadCosmeticPatches(**{field_name: True})  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("slider_name", "label_name", "field_name"),
    [
        ("music_slider", "music_label", "music_volume"),
        ("sfx_slider", "sfx_label", "sfx_volume"),
        ("ambience_slider", "ambience_label", "ambience_volume"),
    ],
)
def test_certain_slider(skip_qtbot: pytestqt.qtbot.QtBot, slider_name: str, label_name: str, field_name: str) -> None:
    cosmetic_patches = DreadCosmeticPatches(**{field_name: 0})  # type: ignore[arg-type]

    dialog = DreadCosmeticPatchesDialog(None, cosmetic_patches)
    label = getattr(dialog, label_name)
    skip_qtbot.addWidget(dialog)
    assert label.text() == "  0%"

    slider = getattr(dialog, slider_name)
    slider.setValue(80)

    assert dialog.cosmetic_patches == DreadCosmeticPatches(**{field_name: 80})  # type: ignore[arg-type]
    assert label.text() == " 80%"


def test_room_names_dropdown(skip_qtbot: pytestqt.qtbot.QtBot) -> None:
    cosmetic_patches = DreadCosmeticPatches(show_room_names=DreadRoomGuiType.NONE)

    dialog = DreadCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    set_combo_with_value(dialog.room_names_dropdown, DreadRoomGuiType.WITH_FADE)

    assert dialog.cosmetic_patches == DreadCosmeticPatches(show_room_names=DreadRoomGuiType.WITH_FADE)


def test_missile_cosmetic_dropdown(skip_qtbot: pytestqt.qtbot.QtBot) -> None:
    cosmetic_patches = DreadCosmeticPatches(missile_cosmetic=DreadMissileCosmeticType.NONE)

    dialog = DreadCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    set_combo_with_value(dialog.missile_cosmetic_dropdown, DreadMissileCosmeticType.TRANS)

    assert dialog.cosmetic_patches == DreadCosmeticPatches(missile_cosmetic=DreadMissileCosmeticType.TRANS)


@pytest.mark.parametrize(
    ("widget_field", "field_name"),
    [
        ("alt_ice_missile", "alt_ice_missile"),
        ("alt_storm_missile", "alt_storm_missile"),
        ("alt_diffusion_beam", "alt_diffusion_beam"),
        ("alt_bomb", "alt_bomb"),
        ("alt_cross_bomb", "alt_cross_bomb"),
        ("alt_power_bomb", "alt_power_bomb"),
    ],
)
def test_shield_type_field(skip_qtbot: pytestqt.qtbot.QtBot, widget_field: str, field_name: str) -> None:
    cosmetic_patches = DreadCosmeticPatches(**{field_name: DreadShieldType.DEFAULT})  # type: ignore[arg-type]

    dialog = DreadCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    # test checking box
    skip_qtbot.mouseClick(getattr(dialog, widget_field), QtCore.Qt.MouseButton.LeftButton)
    assert dialog.cosmetic_patches == DreadCosmeticPatches(
        **{field_name: DreadShieldType.ALTERNATE}  # type: ignore[arg-type]
    )

    # test unchecking box
    skip_qtbot.mouseClick(getattr(dialog, widget_field), QtCore.Qt.MouseButton.LeftButton)
    assert dialog.cosmetic_patches == DreadCosmeticPatches(
        **{field_name: DreadShieldType.DEFAULT}  # type: ignore[arg-type]
    )
