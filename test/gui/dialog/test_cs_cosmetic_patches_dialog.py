from PySide6 import QtCore

from randovania.games.cave_story.gui.dialog.cs_cosmetic_patches_dialog import CSCosmeticPatchesDialog
from randovania.games.cave_story.layout.cs_cosmetic_patches import CSCosmeticPatches, CSMusic, CSSong, MusicRandoType, \
    MyChar


def test_change_mychar(skip_qtbot):
    cosmetic_patches = CSCosmeticPatches()

    dialog = CSCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    skip_qtbot.mouseClick(dialog.mychar_left_button, QtCore.Qt.LeftButton)

    assert dialog.cosmetic_patches == CSCosmeticPatches(mychar=MyChar.CUSTOM)


def test_change_music_rando(skip_qtbot):
    cosmetic_patches = CSCosmeticPatches(
        music_rando=CSMusic(randomization_type=MusicRandoType.CHAOS, song_status=CSSong.all_songs_enabled()))

    dialog = CSCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    assert dialog.song_beta_check.isChecked()
    assert dialog.song_kero_check.isChecked()

    # Using mouseClick isn't working for unknown reasons
    # skip_qtbot.mouseClick(dialog.song_beta_check, QtCore.Qt.LeftButton)
    dialog.song_beta_check.setChecked(False)

    skip_qtbot.mouseClick(dialog.song_kero_check, QtCore.Qt.LeftButton)
    dialog.music_type_combo.setCurrentIndex(0)

    assert not dialog.song_beta_check.isChecked()
    assert not dialog.song_kero_check.isChecked()

    expected = CSCosmeticPatches()
    assert dialog.cosmetic_patches == expected
