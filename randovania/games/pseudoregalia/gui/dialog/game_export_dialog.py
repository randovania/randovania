from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import TYPE_CHECKING

from randovania.game.game_enum import RandovaniaGame
from randovania.games.pseudoregalia.exporter.game_exporter import PseudoregaliaGameExportParams
from randovania.games.pseudoregalia.exporter.options import PseudoregaliaPerGameOptions
from randovania.games.pseudoregalia.gui.generated.pseudoregalia_game_export_dialog_ui import (
    Ui_PseudoregaliaGameExportDialog,
)
from randovania.games.pseudoregalia.layout import PseudoregaliaConfiguration
from randovania.gui.dialog.game_export_dialog import (
    GameExportDialog,
    add_field_validation,
    prompt_for_output_directory,
    spoiler_path_for,
)

if TYPE_CHECKING:
    from PySide6.QtWidgets import QLineEdit

    from randovania.interface_common.options import PerGameOptions


def game_dir_validator(line_edit: QLineEdit) -> bool:
    line_edit_path = Path(line_edit.text())
    pak_path = line_edit_path.joinpath("pseudoregalia", "Content", "Paks", "psuedoregalia-Windows.pak")
    return line_edit_path.is_dir() and pak_path.exists()


class PseudoregaliaGameExportDialog(GameExportDialog[PseudoregaliaConfiguration], Ui_PseudoregaliaGameExportDialog):
    """A window for asking the user for what is needed to export this specific game.

    The provided implementation assumes you need an ISO/ROM file, and produces a new ISO/ROM file."""

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.PSEUDOREGALIA

    def __init__(self, options, configuration, word_hash, spoiler, games):
        super().__init__(options, configuration, word_hash, spoiler, games)
        per_game = options.per_game_options(PseudoregaliaPerGameOptions)

        # Output
        self.default_button.clicked.connect(self._on_default_button)
        self.game_dir_button.clicked.connect(self._on_game_dir_button)

        if per_game.game_dir is not None:
            self.game_dir_edit.setText(str(per_game.game_dir))
        else:
            self._on_default_button()

        add_field_validation(
            accept_button=self.accept_button,
            fields={
                self.game_dir_edit: lambda: game_dir_validator(self.game_dir_edit),
            },
        )

    @property
    def game_dir(self) -> Path:
        return Path(self.game_dir_edit.text())

    @property
    def auto_save_spoiler(self) -> bool:
        return self.auto_save_spoiler_check.isChecked()

    def _on_default_button(self) -> None:
        self.game_dir_edit.setText("C:/Program Files (x86)/Steam/steamapps/common/pseudoregalia")

    def _on_game_dir_button(self) -> None:
        game_dir = prompt_for_output_directory(self, "Pseudoregalia Directory", self.game_dir_edit)
        if game_dir is not None:
            self.game_dir_edit.setText(str(game_dir))

    def update_per_game_options(self, per_game: PerGameOptions) -> PseudoregaliaPerGameOptions:
        assert isinstance(per_game, PseudoregaliaPerGameOptions)
        return dataclasses.replace(
            per_game,
            game_dir=self.game_dir,
        )

    def get_game_export_params(self) -> PseudoregaliaGameExportParams:
        """Creates the GameExportParams for this specific game,
        based on the data provided by the user in this window."""

        spoiler_output = spoiler_path_for(self.auto_save_spoiler, self.game_dir)

        return PseudoregaliaGameExportParams(
            spoiler_output=spoiler_output,
            game_dir=self.game_dir,
        )
