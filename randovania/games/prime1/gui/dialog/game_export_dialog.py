from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import TYPE_CHECKING

from randovania.game.game_enum import RandovaniaGame
from randovania.games.common.prime_family.gui.export_validator import is_prime1_iso_validator, is_prime2_iso_validator
from randovania.games.prime1.exporter.game_exporter import PrimeGameExportParams
from randovania.games.prime1.exporter.options import PrimePerGameOptions
from randovania.games.prime1.gui.generated.prime_game_export_dialog_ui import Ui_PrimeGameExportDialog
from randovania.games.prime1.layout.prime_configuration import PrimeConfiguration
from randovania.games.prime2.exporter.options import EchoesPerGameOptions
from randovania.gui.dialog.game_export_dialog import (
    GameExportDialog,
    add_field_validation,
    output_file_validator,
    prompt_for_input_file,
    prompt_for_output_file,
    spoiler_path_for,
    update_validation,
)
from randovania.gui.lib.multi_format_output_mixin import MultiFormatOutputMixin

if TYPE_CHECKING:
    from randovania.exporter.game_exporter import GameExportParams
    from randovania.interface_common.options import Options


class PrimeGameExportDialog(GameExportDialog[PrimeConfiguration], MultiFormatOutputMixin, Ui_PrimeGameExportDialog):
    _use_echoes_models: bool

    @classmethod
    def game_enum(cls):
        return RandovaniaGame.METROID_PRIME

    def __init__(
        self,
        options: Options,
        configuration: PrimeConfiguration,
        word_hash: str,
        spoiler: bool,
        games: list[RandovaniaGame],
    ):
        super().__init__(options, configuration, word_hash, spoiler, games)

        self.has_enemy_attribute_rando = configuration.enemy_attributes is not None

        self._base_output_name = f"Prime Randomizer - {word_hash}"
        per_game = options.per_game_options(PrimePerGameOptions)

        # Input
        self.input_file_button.clicked.connect(self._on_input_file_button)

        # Output
        self.output_file_button.clicked.connect(self._on_output_file_button)

        # Output format
        self.setup_multi_format(per_game.output_format)
        if self.has_enemy_attribute_rando:
            for radio in self.format_radio_buttons.values():
                if not radio.isEnabled():
                    radio.setToolTip("Format unavailable when Enemy Attribute Randomizer is enabled.")

        # Echoes input
        self.echoes_file_button.clicked.connect(self._on_echoes_file_button)

        # Echoes ISO input
        if RandovaniaGame.METROID_PRIME_ECHOES in games:
            self._use_echoes_models = RandovaniaGame.METROID_PRIME_ECHOES in per_game.use_external_models
            self.echoes_models_check.setChecked(self._use_echoes_models)
            self._on_echoes_models_check()
            self.echoes_models_check.clicked.connect(self._on_echoes_models_check)

            echoes_options = options.per_game_options(EchoesPerGameOptions)
            if echoes_options.input_path is not None:
                self.echoes_file_edit.setText(str(echoes_options.input_path))

        else:
            self._use_echoes_models = False
            self.echoes_models_check.hide()
            self.echoes_file_edit.hide()
            self.echoes_file_label.hide()
            self.echoes_file_button.hide()

        if per_game.input_path is not None:
            self.input_file_edit.setText(str(per_game.input_path))

        if per_game.output_directory is not None:
            output_path = per_game.output_directory.joinpath(self.default_output_name)
            self.output_file_edit.setText(str(output_path))

        add_field_validation(
            accept_button=self.accept_button,
            fields={
                self.input_file_edit: lambda: is_prime1_iso_validator(self.input_file),
                self.output_file_edit: lambda: output_file_validator(self.output_file),
                self.echoes_file_edit: lambda: self._use_echoes_models and is_prime2_iso_validator(self.echoes_file),
            },
        )

    @property
    def valid_input_file_types(self) -> list[str]:
        return ["iso"]

    @property
    def valid_output_file_types(self) -> list[str]:
        return ["iso", "ciso", "gcz"]

    @property
    def available_output_file_types(self) -> list[str]:
        if self.has_enemy_attribute_rando:
            return ["iso"]
        else:
            return self.valid_output_file_types

    def update_per_game_options(self, per_game: PrimePerGameOptions) -> PrimePerGameOptions:
        use_external_models = per_game.use_external_models.copy()
        if not self.echoes_models_check.isHidden():
            if self._use_echoes_models:
                use_external_models.add(RandovaniaGame.METROID_PRIME_ECHOES)
            else:
                use_external_models.discard(RandovaniaGame.METROID_PRIME_ECHOES)

        return dataclasses.replace(
            per_game,
            input_path=self.input_file,
            output_directory=self.output_file.parent,
            output_format=(per_game.output_format if self.has_enemy_attribute_rando else self._selected_output_format),
            use_external_models=use_external_models,
        )

    def save_options(self):
        super().save_options()
        if not self._use_echoes_models:
            return

        with self._options as options:
            from randovania.games.prime2.exporter.options import EchoesPerGameOptions

            options.set_per_game_options(
                dataclasses.replace(
                    options.per_game_options(EchoesPerGameOptions),
                    input_path=self.echoes_file,
                ),
            )

    # Getters
    @property
    def input_file(self) -> Path:
        return Path(self.input_file_edit.text())

    @property
    def output_file(self) -> Path:
        return Path(self.output_file_edit.text())

    @property
    def echoes_file(self) -> Path | None:
        if self._use_echoes_models:
            return Path(self.echoes_file_edit.text())

    @property
    def auto_save_spoiler(self) -> bool:
        return self.auto_save_spoiler_check.isChecked()

    # Input file
    def _on_input_file_button(self):
        input_file = prompt_for_input_file(self, self.input_file_edit, self.valid_input_file_types)
        if input_file is not None:
            self.input_file_edit.setText(str(input_file.absolute()))

    # Output File
    def _on_output_file_button(self):
        output_file = prompt_for_output_file(
            self, self.available_output_file_types, self.default_output_name, self.output_file_edit
        )
        if output_file is not None:
            self.output_file_edit.setText(str(output_file))

    # Echoes input
    def _on_echoes_models_check(self):
        use_echoes_models = self.echoes_models_check.isChecked()
        self._use_echoes_models = use_echoes_models
        self.echoes_file_edit.setEnabled(use_echoes_models)
        self.echoes_file_label.setEnabled(use_echoes_models)
        self.echoes_file_button.setEnabled(use_echoes_models)
        update_validation(self.echoes_file_edit)

    def _on_echoes_file_button(self):
        input_file = prompt_for_input_file(self, self.input_file_edit, ["iso"])
        if input_file is not None:
            self.echoes_file_edit.setText(str(input_file.absolute()))

    def get_game_export_params(self) -> GameExportParams:
        spoiler_output = spoiler_path_for(self.auto_save_spoiler, self.output_file)
        cache_path = self._options.internal_copies_path.joinpath("prime1", "randomprime_cache")
        asset_cache_path = self._options.internal_copies_path.joinpath("prime1", "prime2_models")

        return PrimeGameExportParams(
            spoiler_output=spoiler_output,
            input_path=self.input_file,
            output_path=self.output_file,
            echoes_input_path=self.echoes_file,
            asset_cache_path=asset_cache_path,
            use_echoes_models=self._use_echoes_models,
            cache_path=cache_path,
        )
