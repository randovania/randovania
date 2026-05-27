from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import TYPE_CHECKING, override

from randovania.game.game_enum import RandovaniaGame
from randovania.games.common.prime_family.gui.export_validator import is_prime1_iso_validator, is_prime2_iso_validator
from randovania.games.prime1.exporter.options import PrimePerGameOptions
from randovania.games.prime2_dev.exporter.game_exporter import EchoesGameExportParams
from randovania.games.prime2_dev.exporter.options import EchoesPerGameOptions
from randovania.games.prime2_dev.gui.generated.echoes_game_export_dialog_ui import Ui_EchoesGameExportDialog
from randovania.games.prime2_dev.layout import EchoesConfiguration
from randovania.gui.dialog.game_export_dialog import (
    GameExportDialog,
    add_field_validation,
    output_file_validator,
    prompt_for_input_file,
    prompt_for_output_file,
    spoiler_path_for,
    update_validation,
)

if TYPE_CHECKING:
    from randovania.interface_common.options import Options, PerGameOptions


class EchoesGameExportDialog(GameExportDialog[EchoesConfiguration], Ui_EchoesGameExportDialog):
    """A window for asking the user for what is needed to export this specific game.

    The provided implementation assumes you need an ISO/ROM file, and produces a new ISO/ROM file."""

    _use_prime_models: bool

    def __init__(
        self,
        options: Options,
        configuration: EchoesConfiguration,
        word_hash: str,
        spoiler: bool,
        games: list[RandovaniaGame],
    ):
        super().__init__(options, configuration, word_hash, spoiler, games)
        self.default_output_name = f"Echoes Randomizer - {word_hash}"

        per_game = options.per_game_options(EchoesPerGameOptions)

        # Input
        self.input_file_button.clicked.connect(self._on_input_file_button)

        # Output
        self.output_file_button.clicked.connect(self._on_output_file_button)

        # Prime input
        self.prime_file_button.clicked.connect(self._on_prime_file_button)

        if RandovaniaGame.METROID_PRIME in games:
            self._use_prime_models = RandovaniaGame.METROID_PRIME in per_game.use_external_models
            self.prime_models_check.setChecked(self._use_prime_models)
            self._on_prime_models_check()
            self.prime_models_check.clicked.connect(self._on_prime_models_check)

            prime_options = options.per_game_options(PrimePerGameOptions)
            if prime_options.input_path is not None:
                self.prime_file_edit.setText(str(prime_options.input_path))

        else:
            self._use_prime_models = False
            self.prime_models_check.hide()
            self.prime_file_edit.hide()
            self.prime_file_label.hide()
            self.prime_file_button.hide()

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
                self.prime_file_edit: lambda: (
                    self._use_prime_models and is_prime1_iso_validator(self.prime_file, iso_required=True)
                ),
            },
        )

    @override
    def update_per_game_options(self, per_game: PerGameOptions) -> EchoesPerGameOptions:
        assert isinstance(per_game, EchoesPerGameOptions)

        use_external_models = per_game.use_external_models.copy()
        if not self.prime_models_check.isHidden():
            if self._use_prime_models:
                use_external_models.add(RandovaniaGame.METROID_PRIME)
            else:
                use_external_models.discard(RandovaniaGame.METROID_PRIME)

        return dataclasses.replace(
            per_game,
            input_path=self.input_file,
            output_path=self.output_file,
            use_external_models=use_external_models,
        )

    @override
    def save_options(self) -> None:
        super().save_options()
        if not self._use_prime_models:
            return

        with self._options as options:
            from randovania.games.prime1.exporter.options import PrimePerGameOptions

            options.set_per_game_options(
                dataclasses.replace(
                    options.per_game_options(PrimePerGameOptions),
                    input_path=self.prime_file,
                ),
            )

    # Getters

    @override
    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_PRIME_ECHOES_DEV

    @property
    def input_file(self) -> Path:
        return Path(self.input_file_edit.text())

    @property
    def output_file(self) -> Path:
        return Path(self.output_file_edit.text())

    @property
    def prime_file(self) -> Path | None:
        if text := self.prime_file_edit.text():
            return Path(text)
        return None

    @override
    @property
    def auto_save_spoiler(self) -> bool:
        return self.auto_save_spoiler_check.isChecked()

    # Checks

    # Input file
    def _on_input_file_button(self) -> None:
        input_file = prompt_for_input_file(self, self.input_file_edit, ["iso"])
        if input_file is not None:
            self.input_file_edit.setText(str(input_file.absolute()))

    # Output File
    def _on_output_file_button(self) -> None:
        output_file = prompt_for_output_file(self, ["iso"], f"{self.default_output_name}.iso", self.output_file_edit)
        if output_file is not None:
            self.output_file_edit.setText(str(output_file))

    # Prime input
    def _on_prime_file_button(self) -> None:
        prime_file = prompt_for_input_file(self, self.prime_file_edit, ["iso"])
        if prime_file is not None:
            self.prime_file_edit.setText(str(prime_file.absolute()))

    def _on_prime_models_check(self) -> None:
        use_prime_models = self.prime_models_check.isChecked()
        self._use_prime_models = use_prime_models
        self.prime_file_edit.setEnabled(use_prime_models)
        self.prime_file_label.setEnabled(use_prime_models)
        self.prime_file_button.setEnabled(use_prime_models)
        update_validation(self.prime_file_edit)

    # Export Params

    @override
    def get_game_export_params(self) -> EchoesGameExportParams:
        """Creates the GameExportParams for this specific game,
        based on the data provided by the user in this window."""

        spoiler_output = spoiler_path_for(self.auto_save_spoiler, self.output_file)

        return EchoesGameExportParams(
            spoiler_output=spoiler_output,
            input_path=self.input_file,
            output_path=self.output_file,
        )
