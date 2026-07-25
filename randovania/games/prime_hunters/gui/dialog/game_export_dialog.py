from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import TYPE_CHECKING

from randovania.game.game_enum import RandovaniaGame
from randovania.games.prime_hunters.exporter.game_exporter import HuntersGameExportParams
from randovania.games.prime_hunters.exporter.options import HuntersPerGameOptions
from randovania.games.prime_hunters.gui.generated.prime_hunters_game_export_dialog_ui import Ui_HuntersGameExportDialog
from randovania.games.prime_hunters.layout import HuntersConfiguration
from randovania.gui.dialog.game_export_dialog import (
    GameExportDialog,
    add_field_validation,
    is_file_validator,
    output_file_validator,
    prompt_for_input_file,
    prompt_for_output_file,
    spoiler_path_for,
)

if TYPE_CHECKING:
    from randovania.interface_common.options import Options, PerGameOptions

# Expected rom header data for vanilla "Metroid Prime Hunters.NDS" based on region
EXPECTED_ROM_HEADER_DATA: list[bytes] = [
    b"MP HUNTERS\x00\x00AMHE",  # USA Rev0/Rev1
    b"MP HUNTERS\x00\x00AMHP",  # Europe Rev0/Rev1
    # b"MP HUNTERS\x00\x00AMHJ",  # Japan Rev0
    # b"MP HUNTERS\x00\x00AMHK",  # Korea Rev0
]


def is_hunters_validator(path: Path | None) -> bool:
    """Validates if the given path is a proper input for Hunters.
    - If input doesn't exist, returns True.
    - If input MD5 matches the vanilla MD5, returns False.
    """

    if is_file_validator(path):
        return True
    assert path is not None
    try:
        with path.open("rb") as file:
            rom_header_data = file.read(16)
    except Exception:
        # If any error during opening happens, suppress that and pretend its invalid,
        # as otherwise it would cause the dialog to be inaccessible.
        return True
    if rom_header_data in EXPECTED_ROM_HEADER_DATA:
        return False
    else:
        return True


class HuntersGameExportDialog(GameExportDialog[HuntersConfiguration], Ui_HuntersGameExportDialog):
    """A window for asking the user for what is needed to export this specific game.

    The provided implementation assumes you need an ISO/ROM file, and produces a new ISO/ROM file."""

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_PRIME_HUNTERS

    def __init__(
        self,
        options: Options,
        configuration: HuntersConfiguration,
        word_hash: str,
        spoiler: bool,
        games: list[RandovaniaGame],
    ):
        super().__init__(options, configuration, word_hash, spoiler, games)

        self._base_output_name = f"Prime Hunters - {word_hash}.{self.valid_file_type}"
        hunters_options = options.per_game_options(HuntersPerGameOptions)

        # Input
        self.input_file_button.clicked.connect(self._on_input_file_button)

        # Output
        self.output_file_button.clicked.connect(self._on_output_file_button)

        if hunters_options.input_path is not None:
            self.input_file_edit.setText(str(hunters_options.input_path))

        if hunters_options.output_path is not None:
            output_path = hunters_options.output_path.joinpath(self._base_output_name)
            self.output_file_edit.setText(str(output_path))

        add_field_validation(
            accept_button=self.accept_button,
            fields={
                self.input_file_edit: lambda: is_hunters_validator(self.input_file),
                self.output_file_edit: lambda: output_file_validator(self.output_file),
            },
        )

    @property
    def valid_file_type(self) -> str:
        return "nds"

    @property
    def input_file(self) -> Path:
        return Path(self.input_file_edit.text())

    @property
    def output_file(self) -> Path:
        return Path(self.output_file_edit.text())

    @property
    def auto_save_spoiler(self) -> bool:
        return self.auto_save_spoiler_check.isChecked()

    # Input file
    def _on_input_file_button(self) -> None:
        input_file = prompt_for_input_file(self, self.input_file_edit, [self.valid_file_type])
        if input_file is not None:
            self.input_file_edit.setText(str(input_file.absolute()))

    # Output File
    def _on_output_file_button(self) -> None:
        output_file = prompt_for_output_file(
            self, [self.valid_file_type], self._base_output_name, self.output_file_edit
        )
        if output_file is not None:
            self.output_file_edit.setText(str(output_file))

    def update_per_game_options(self, hunters_options: PerGameOptions) -> HuntersPerGameOptions:
        assert isinstance(hunters_options, HuntersPerGameOptions)
        return dataclasses.replace(
            hunters_options,
            input_path=self.input_file,
            output_path=self.output_file.parent,
        )

    def get_game_export_params(self) -> HuntersGameExportParams:
        """Creates the GameExportParams for this specific game,
        based on the data provided by the user in this window."""

        spoiler_output = spoiler_path_for(self.auto_save_spoiler, self.output_file)

        return HuntersGameExportParams(
            spoiler_output=spoiler_output,
            input_path=self.input_file,
            output_path=self.output_file,
        )
