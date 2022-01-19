from PySide2 import QtCore

from randovania.games.super_metroid.gui.dialog.super_cosmetic_patches_dialog import SuperCosmeticPatchesDialog
from randovania.games.super_metroid.layout.super_metroid_cosmetic_patches import SuperMetroidCosmeticPatches


def test_dialog_checkboxes(skip_qtbot):
    cosmetic_patches = SuperMetroidCosmeticPatches()

    dialog = SuperCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    default_settings = SuperMetroidCosmeticPatches()

    for field_name, checkbox in dialog.checkboxes.items():
        skip_qtbot.mouseClick(checkbox, QtCore.Qt.LeftButton)
        assert getattr(dialog.cosmetic_patches, field_name) == (not getattr(default_settings, field_name))


def test_music_settings(skip_qtbot):
    cosmetic_patches = SuperMetroidCosmeticPatches()

    dialog = SuperCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    for music_mode, radio_button in dialog.radio_buttons.items():
        assert (music_mode == dialog.cosmetic_patches.music) == radio_button.isChecked()
