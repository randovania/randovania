from __future__ import annotations

import dataclasses

from PySide6 import QtGui, QtWidgets

from randovania.games.cave_story.gui.generated.cs_cosmetic_patches_dialog_ui import Ui_CSCosmeticPatchesDialog
from randovania.games.cave_story.layout.cs_cosmetic_patches import (
    CSCosmeticPatches,
    CSSong,
    MusicRandoType,
    MyChar,
    SongGame,
)
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
from randovania.gui.lib import signal_handling
from randovania.gui.lib.signal_handling import set_combo_with_value


class CSCosmeticPatchesDialog(BaseCosmeticPatchesDialog, Ui_CSCosmeticPatchesDialog):
    _cosmetic_patches: CSCosmeticPatches

    def __init__(self, parent: QtWidgets.QWidget | None, current: CSCosmeticPatches):
        super().__init__(parent)
        self.setupUi(self)
        self._cosmetic_patches = current

        for i, value in enumerate(MusicRandoType):
            self.music_type_combo.setItemData(i, value)

        self.on_new_cosmetic_patches(current)
        self.connect_signals()

    def connect_signals(self) -> None:
        super().connect_signals()

        signal_handling.on_combo(self.music_type_combo, self._on_music_type_changed)
        self.mychar_left_button.clicked.connect(self._mychar_left)
        self.mychar_right_button.clicked.connect(self._mychar_right)

        signal_handling.on_checked(self.song_cs_check, self._cs_songs)
        signal_handling.on_checked(self.song_beta_check, self._beta_songs)
        signal_handling.on_checked(self.song_kero_check, self._kero_songs)

    def on_new_cosmetic_patches(self, patches: CSCosmeticPatches) -> None:
        set_combo_with_value(self.music_type_combo, patches.music_rando.randomization_type)
        self._set_mychar(patches.mychar)
        self._read_songs(patches.music_rando.song_status)

    def _on_mychar_changed(self, reverse: bool) -> None:
        new_mychar = self._cosmetic_patches.mychar.next_mychar(reverse)
        self._cosmetic_patches = dataclasses.replace(self._cosmetic_patches, mychar=new_mychar)
        self._set_mychar(new_mychar)

    def _mychar_left(self) -> None:
        self._on_mychar_changed(True)

    def _mychar_right(self) -> None:
        self._on_mychar_changed(False)

    def _set_mychar(self, new_mychar: MyChar) -> None:
        self.mychar_name_label.setText(new_mychar.value)
        self.mychar_img_label.setPixmap(QtGui.QPixmap(str(new_mychar.ui_icon)))
        self.mychar_description_label.setText(new_mychar.description)
        self.mychar_description_label.setVisible(bool(new_mychar.description))

    def _on_music_type_changed(self, combo_enum: MusicRandoType) -> None:
        music_rando = dataclasses.replace(self._cosmetic_patches.music_rando, randomization_type=combo_enum)
        self._cosmetic_patches = dataclasses.replace(self._cosmetic_patches, music_rando=music_rando)
        self.music_type_description_label.setText(combo_enum.description)

    def _cs_songs(self, value: bool) -> None:
        self._set_songs(SongGame.CS, value)

    def _beta_songs(self, value: bool) -> None:
        self._set_songs(SongGame.BETA, value)

    def _kero_songs(self, value: bool) -> None:
        self._set_songs(SongGame.KERO, value)

    def _set_songs(self, game: SongGame, enabled: bool) -> None:
        new_status: dict[str, bool] = {}
        for name in self._cosmetic_patches.music_rando.song_status.keys():
            song = CSSong.from_name(name)
            if song.source_game == game:
                new_status[name] = enabled

        self._cosmetic_patches = dataclasses.replace(
            self._cosmetic_patches, music_rando=self._cosmetic_patches.music_rando.update_song_status(new_status)
        )

    def _read_songs(self, status: dict[str, bool]) -> None:
        self.song_cs_check.setChecked(False)
        self.song_beta_check.setChecked(False)
        self.song_kero_check.setChecked(False)

        for name, enabled in status.items():
            if enabled:
                song = CSSong.from_name(name)
                if song.source_game == SongGame.CS:
                    self.song_cs_check.setChecked(True)
                elif song.source_game == SongGame.BETA:
                    self.song_beta_check.setChecked(True)
                elif song.source_game == SongGame.KERO:
                    self.song_kero_check.setChecked(True)

    @property
    def cosmetic_patches(self) -> CSCosmeticPatches:
        return self._cosmetic_patches

    def reset(self) -> None:
        self.on_new_cosmetic_patches(CSCosmeticPatches())
