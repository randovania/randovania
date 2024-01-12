from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.games.factorio.exporter.game_exporter import FactorioGameExportParams
from randovania.games.factorio.exporter.options import FactorioPerGameOptions
from randovania.games.game import RandovaniaGame
from randovania.gui.dialog.game_export_dialog import GameExportDialog

if TYPE_CHECKING:
    from pathlib import Path

    from randovania.interface_common.options import PerGameOptions


class FactorioGameExportDialog(GameExportDialog):
    """A window for asking the user for what is needed to export this specific game.

    The provided implementation assumes you need an ISO/ROM file, and produces a new ISO/ROM file."""

    def setupUi(self, obj):
        self.accept_button = QtWidgets.QPushButton("DO IT", self)

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.FACTORIO

    @property
    def input_file(self) -> Path:
        raise NotImplementedError("This method hasn't been implemented yet")

    @property
    def output_file(self) -> Path:
        raise NotImplementedError("This method hasn't been implemented yet")

    @property
    def auto_save_spoiler(self) -> bool:
        return False

    def update_per_game_options(self, per_game: PerGameOptions) -> FactorioPerGameOptions:
        assert isinstance(per_game, FactorioPerGameOptions)
        return dataclasses.replace(
            per_game,
            # input_path=self.input_file,
            # output_path=self.output_file,
        )

    def get_game_export_params(self) -> FactorioGameExportParams:
        """Creates the GameExportParams for this specific game,
        based on the data provided by the user in this window."""

        # spoiler_output = spoiler_path_for(self.auto_save_spoiler, self.output_file)

        return FactorioGameExportParams(
            spoiler_output=None,
            # input_path=self.input_file,
            # output_path=self.output_file,
        )
