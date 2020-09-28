from randovania.gui.dialog.echoes_user_preferences_dialog import EchoesUserPreferencesDialog
from randovania.interface_common.cosmetic_patches import CosmeticPatches
from randovania.interface_common.echoes_user_preferences import EchoesUserPreferences, SoundMode


def test_change_sound_mode(skip_qtbot):
    preferences = CosmeticPatches(user_preferences=EchoesUserPreferences(sound_mode=SoundMode.MONO))

    dialog = EchoesUserPreferencesDialog(None, preferences)
    skip_qtbot.addWidget(dialog)

    dialog.sound_mode_combo.setCurrentIndex(2)

    assert dialog.preferences == EchoesUserPreferences(sound_mode=SoundMode.SURROUND)


def test_change_sfx_volume(skip_qtbot):
    preferences = CosmeticPatches(user_preferences=EchoesUserPreferences(sfx_volume=15))

    dialog = EchoesUserPreferencesDialog(None, preferences)
    skip_qtbot.addWidget(dialog)

    dialog.sfx_volume_slider.setValue(50)

    assert dialog.preferences == EchoesUserPreferences(sfx_volume=50)


def test_change_hud_lag(skip_qtbot):
    preferences = CosmeticPatches(user_preferences=EchoesUserPreferences(hud_lag=False))

    dialog = EchoesUserPreferencesDialog(None, preferences)
    skip_qtbot.addWidget(dialog)

    dialog.hud_lag_check.setChecked(True)

    assert dialog.preferences == EchoesUserPreferences(hud_lag=True)
