from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtCore

from randovania.games.prime2.gui.dialog.echoes_cosmetic_patches_dialog import EchoesCosmeticPatchesDialog
from randovania.games.prime2.layout.echoes_cosmetic_patches import EchoesCosmeticPatches
from randovania.games.prime2.layout.echoes_user_preferences import EchoesUserPreferences, SoundMode

if TYPE_CHECKING:
    import pytestqt.qtbot  # type: ignore[import]


def test_suit_cosmetics(skip_qtbot: pytestqt.qtbot.QtBot) -> None:
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


def test_change_sound_mode(skip_qtbot: pytestqt.qtbot.QtBot) -> None:
    preferences = EchoesCosmeticPatches(user_preferences=EchoesUserPreferences(sound_mode=SoundMode.MONO))

    dialog = EchoesCosmeticPatchesDialog(None, preferences)
    skip_qtbot.addWidget(dialog)

    dialog.sound_mode_combo.setCurrentIndex(2)

    assert dialog.preferences == EchoesUserPreferences(sound_mode=SoundMode.SURROUND)


def test_change_sfx_volume(skip_qtbot: pytestqt.qtbot.QtBot) -> None:
    preferences = EchoesCosmeticPatches(user_preferences=EchoesUserPreferences(sfx_volume=15))

    dialog = EchoesCosmeticPatchesDialog(None, preferences)
    skip_qtbot.addWidget(dialog)

    dialog.sfx_volume_slider.setValue(50)

    assert dialog.preferences == EchoesUserPreferences(sfx_volume=50)


def test_change_hud_lag(skip_qtbot: pytestqt.qtbot.QtBot) -> None:
    preferences = EchoesCosmeticPatches(user_preferences=EchoesUserPreferences(hud_lag=False))

    dialog = EchoesCosmeticPatchesDialog(None, preferences)
    skip_qtbot.addWidget(dialog)

    dialog.hud_lag_check.setChecked(True)

    assert dialog.preferences == EchoesUserPreferences(hud_lag=True)
