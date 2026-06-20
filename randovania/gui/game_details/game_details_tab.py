from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6 import QtWidgets

    from randovania.game.game_enum import RandovaniaGame
    from randovania.game_description.game_patches import GamePatches
    from randovania.interface_common.players_configuration import PlayersConfiguration
    from randovania.layout.base.base_configuration import BaseConfiguration


class GameDetailsTab[ConfigurationT: BaseConfiguration]:
    def __init__(self, parent: QtWidgets.QWidget, game: RandovaniaGame) -> None:
        self.game_enum = game

    def widget(self) -> QtWidgets.QWidget:
        raise NotImplementedError

    def tab_title(self) -> str:
        raise NotImplementedError

    def update_content(
        self, configuration: ConfigurationT, all_patches: dict[int, GamePatches], players: PlayersConfiguration
    ) -> None:
        raise NotImplementedError

    @classmethod
    def should_appear_for(
        cls, configuration: ConfigurationT, all_patches: dict[int, GamePatches], players: PlayersConfiguration
    ) -> bool:
        return True
