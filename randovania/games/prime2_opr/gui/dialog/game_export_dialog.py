from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import TYPE_CHECKING, override

from randovania.game.game_enum import RandovaniaGame
from randovania.games.common.prime_family.gui.export_validator import is_prime2_iso_validator
from randovania.games.prime2_opr.exporter.game_exporter import EchoesOPRGameExportParams
from randovania.games.prime2_opr.exporter.options import EchoesOPRPerGameOptions
from randovania.games.prime2_opr.gui.generated.prime2_opr_game_export_dialog_ui import Ui_EchoesOPRGameExportDialog
from randovania.games.prime2_opr.layout import EchoesOPRConfiguration
from randovania.gui.dialog.game_export_dialog import (
    GameExportDialog,
    add_field_validation,
    output_file_validator,
    prompt_for_input_file,
    prompt_for_output_file,
    spoiler_path_for,
)
from randovania.interface_common.options import Options

if TYPE_CHECKING:
    from randovania.interface_common.options import PerGameOptions


class EchoesOPRGameExportDialog(GameExportDialog[EchoesOPRConfiguration], Ui_EchoesOPRGameExportDialog):
    """A window for asking the user for what is needed to export this specific game.

    The provided implementation assumes you need an ISO/ROM file, and produces a new ISO/ROM file."""

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_PRIME_ECHOES_OPR

    def __init__(
        self,
        options: Options,
        configuration: EchoesOPRConfiguration,
        word_hash: str,
        spoiler: bool,
        games: list[RandovaniaGame],
    ):
        super().__init__(options, configuration, word_hash, spoiler, games)

        self.default_output_name = f"Echoes OPR - {word_hash}"

        self.input_file_button.clicked.connect(self._on_input_file_button)
        self.output_file_button.clicked.connect(self._on_output_file_button)

        per_game = options.per_game_options(EchoesOPRPerGameOptions)

        # TODO: nod-rs supports more formats than just ISO, so we can too

        if per_game.input_path is not None:
            self.input_file_edit.setText(str(per_game.input_path))

        if per_game.output_directory is not None:
            output_path = per_game.output_directory.joinpath(f"{self.default_output_name}.iso")
            self.output_file_edit.setText(str(output_path))

        add_field_validation(
            accept_button=self.accept_button,
            fields={
                self.input_file_edit: lambda: is_prime2_iso_validator(self.input_file),
                self.output_file_edit: lambda: output_file_validator(self.output_file),
            },
        )

    @property
    def input_file(self) -> Path:
        return Path(self.input_file_edit.text())

    @property
    def output_file(self) -> Path:
        return Path(self.output_file_edit.text())

    @override
    @property
    def auto_save_spoiler(self) -> bool:
        return self.auto_save_spoiler_check.isChecked()

    @override
    def update_per_game_options(self, per_game: PerGameOptions) -> EchoesOPRPerGameOptions:
        assert isinstance(per_game, EchoesOPRPerGameOptions)
        return dataclasses.replace(
            per_game,
            input_path=self.input_file,
            output_directory=self.output_file.parent,
        )

    @override
    def get_game_export_params(self) -> EchoesOPRGameExportParams:
        """Creates the GameExportParams for this specific game,
        based on the data provided by the user in this window."""

        spoiler_output = spoiler_path_for(self.auto_save_spoiler, self.output_file)

        return EchoesOPRGameExportParams(
            spoiler_output=spoiler_output,
            input_path=self.input_file,
            output_path=self.output_file,
        )

    def _on_input_file_button(self) -> None:
        input_file = prompt_for_input_file(self, self.input_file_edit, ["iso"])
        if input_file is not None:
            self.input_file_edit.setText(str(input_file.absolute()))

    def _on_output_file_button(self) -> None:
        output_file = prompt_for_output_file(self, ["iso"], f"{self.default_output_name}.iso", self.output_file_edit)
        if output_file is not None:
            self.output_file_edit.setText(str(output_file))
