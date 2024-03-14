from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.games.fusion.exporter.game_exporter import FusionGameExportParams
from randovania.games.fusion.exporter.options import FusionPerGameOptions
from randovania.games.game import RandovaniaGame
from randovania.gui.dialog.game_export_dialog import GameExportDialog, spoiler_path_for
from randovania.gui.generated.fusion_game_export_dialog_ui import Ui_FusionGameExportDialog

if TYPE_CHECKING:
    from pathlib import Path

    from randovania.interface_common.options import PerGameOptions


# TODO
class FusionGameExportDialog(GameExportDialog, Ui_FusionGameExportDialog):
    """A window for asking the user for what is needed to export this specific game.

    The provided implementation assumes you need an ISO/ROM file, and produces a new ISO/ROM file."""

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.FUSION

    @property
    def input_file(self) -> Path:
        raise NotImplementedError("This method hasn't been implemented yet")

    @property
    def output_file(self) -> Path:
        raise NotImplementedError("This method hasn't been implemented yet")

    @property
    def auto_save_spoiler(self) -> bool:
        raise NotImplementedError("This method hasn't been implemented yet")

    def update_per_game_options(self, per_game: PerGameOptions) -> FusionPerGameOptions:
        assert isinstance(per_game, FusionPerGameOptions)
        return dataclasses.replace(
            per_game,
            input_path=self.input_file,
            output_path=self.output_file,
        )

    def get_game_export_params(self) -> FusionGameExportParams:
        """Creates the GameExportParams for this specific game,
        based on the data provided by the user in this window."""

        spoiler_output = spoiler_path_for(self.auto_save_spoiler, self.output_file)

        return FusionGameExportParams(
            spoiler_output=spoiler_output,
            input_path=self.input_file,
            output_path=self.output_file,
        )
