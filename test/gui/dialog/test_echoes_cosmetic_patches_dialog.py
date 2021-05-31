from randovania.gui.dialog.echoes_cosmetic_patches_dialog import EchoesCosmeticPatchesDialog
from randovania.layout.prime2.echoes_cosmetic_patches import EchoesCosmeticPatches
from randovania.layout.prime2.echoes_user_preferences import EchoesUserPreferences, SoundMode


def test_change_sound_mode(skip_qtbot):
    preferences = EchoesCosmeticPatches(user_preferences=EchoesUserPreferences(sound_mode=SoundMode.MONO))

    dialog = EchoesCosmeticPatchesDialog(None, preferences)
    skip_qtbot.addWidget(dialog)

    dialog.sound_mode_combo.setCurrentIndex(2)

    assert dialog.preferences == EchoesUserPreferences(sound_mode=SoundMode.SURROUND)


def test_change_sfx_volume(skip_qtbot):
    preferences = EchoesCosmeticPatches(user_preferences=EchoesUserPreferences(sfx_volume=15))

    dialog = EchoesCosmeticPatchesDialog(None, preferences)
    skip_qtbot.addWidget(dialog)

    dialog.sfx_volume_slider.setValue(50)

    assert dialog.preferences == EchoesUserPreferences(sfx_volume=50)


def test_change_hud_lag(skip_qtbot):
    preferences = EchoesCosmeticPatches(user_preferences=EchoesUserPreferences(hud_lag=False))

    dialog = EchoesCosmeticPatchesDialog(None, preferences)
    skip_qtbot.addWidget(dialog)

    dialog.hud_lag_check.setChecked(True)

    assert dialog.preferences == EchoesUserPreferences(hud_lag=True)
