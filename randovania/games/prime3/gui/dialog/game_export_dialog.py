from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.games.game import RandovaniaGame
from randovania.games.prime3.exporter.game_exporter import CorruptionGameExportParams
from randovania.games.prime3.exporter.options import CorruptionPerGameOptions
from randovania.gui.dialog.game_export_dialog import GameExportDialog, spoiler_path_for
from randovania.gui.generated.corruption_game_export_dialog_ui import Ui_CorruptionGameExportDialog
from randovania.gui.lib import common_qt_lib

if TYPE_CHECKING:
    from pathlib import Path

    from randovania.interface_common.options import Options, PerGameOptions


class CorruptionGameExportDialog(GameExportDialog, Ui_CorruptionGameExportDialog):
    """A window for asking the user for what is needed to export this specific game.

    The provided implementation assumes you need an ISO/ROM file, and produces a new ISO/ROM file."""

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_PRIME_CORRUPTION

    def __init__(self, options: Options, patch_data: dict, word_hash: str, spoiler: bool, games: list[RandovaniaGame]):
        super().__init__(options, patch_data, word_hash, spoiler, games)
        per_game = options.options_for_game(self.game_enum())
        assert isinstance(per_game, CorruptionPerGameOptions)

        commands = patch_data["commands"]
        common_qt_lib.set_clipboard(commands)
        self.commands_label.setText(commands)

    @property
    def input_file(self) -> Path:
        raise NotImplementedError("This method hasn't been implemented yet")

    @property
    def output_file(self) -> Path:
        raise NotImplementedError("This method hasn't been implemented yet")

    @property
    def auto_save_spoiler(self) -> bool:
        raise NotImplementedError("This method hasn't been implemented yet")

    def update_per_game_options(self, per_game: PerGameOptions) -> CorruptionPerGameOptions:
        assert isinstance(per_game, CorruptionPerGameOptions)
        return dataclasses.replace(
            per_game,
            input_path=self.input_file,
            output_path=self.output_file,
        )

    def get_game_export_params(self) -> CorruptionGameExportParams:
        """Creates the GameExportParams for this specific game,
        based on the data provided by the user in this window."""

        spoiler_output = spoiler_path_for(self.auto_save_spoiler, self.output_file)

        return CorruptionGameExportParams(
            spoiler_output=spoiler_output,
            input_path=self.input_file,
            output_path=self.output_file,
        )
