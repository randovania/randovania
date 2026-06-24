from __future__ import annotations

import typing
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from PySide6 import QtWidgets

    from randovania.game.game_enum import RandovaniaGame
    from randovania.game_description.game_patches import GamePatches
    from randovania.interface_common.players_configuration import PlayersConfiguration
    from randovania.layout.base.base_configuration import BaseConfiguration


class CreateWhenRelevantMethod(typing.Protocol):
    def __call__(
        self,
        parent: QtWidgets.QWidget,
        configuration: BaseConfiguration,
        all_patches: dict[int, GamePatches],
        players: PlayersConfiguration,
    ) -> GameDetailsTab | None: ...


class GameDetailsTab:
    def __init__(self, parent: QtWidgets.QWidget, game: RandovaniaGame):
        self.game_enum = game

    def widget(self) -> QtWidgets.QWidget:
        raise NotImplementedError

    def tab_title(self) -> str:
        raise NotImplementedError

    def update_content(
        self, configuration: BaseConfiguration, all_patches: dict[int, GamePatches], players: PlayersConfiguration
    ):
        raise NotImplementedError

    @classmethod
    def should_appear_for(
        cls, configuration: BaseConfiguration, all_patches: dict[int, GamePatches], players: PlayersConfiguration
    ) -> bool:
        return True

    @classmethod
    def create_when_relevant(
        cls,
        parent: QtWidgets.QWidget,
        configuration: BaseConfiguration,
        all_patches: dict[int, GamePatches],
        players: PlayersConfiguration,
    ) -> Self | None:
        """Creates an instance of this class when `should_appear_for` returns True, None otherwise."""
        if cls.should_appear_for(configuration, all_patches, players):
            return cls(parent, configuration.game)
        return None
