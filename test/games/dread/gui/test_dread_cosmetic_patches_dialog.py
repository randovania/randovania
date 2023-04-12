import pytest
from PySide6 import QtCore

from randovania.games.dread.gui.dialog.dread_cosmetic_patches_dialog import DreadCosmeticPatchesDialog
from randovania.games.dread.layout.dread_cosmetic_patches import DreadCosmeticPatches, DreadRoomGuiType


@pytest.mark.parametrize(["widget_field", "field_name"], [
    ("show_boss_life", "show_boss_lifebar"),
    ("show_enemy_life", "show_enemy_life"),
    ("show_enemy_damage", "show_enemy_damage"),
    ("show_player_damage", "show_player_damage"),
    ("show_death_counter", "show_death_counter"),
])
def test_certain_field(skip_qtbot, widget_field, field_name):
    cosmetic_patches = DreadCosmeticPatches(**{field_name: False})

    dialog = DreadCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    skip_qtbot.mouseClick(getattr(dialog, widget_field), QtCore.Qt.MouseButton.LeftButton)

    assert dialog.cosmetic_patches == DreadCosmeticPatches(**{field_name: True})


def test_room_names_dropdown(skip_qtbot):
    cosmetic_patches = DreadCosmeticPatches(show_room_names=DreadRoomGuiType.NONE)

    dialog = DreadCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    skip_qtbot.keyClicks(dialog.room_names_dropdown, DreadRoomGuiType.WITH_FADE.long_name)

    assert dialog.cosmetic_patches == DreadCosmeticPatches(show_room_names=DreadRoomGuiType.WITH_FADE)
