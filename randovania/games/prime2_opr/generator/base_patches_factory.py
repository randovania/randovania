from __future__ import annotations

import typing
from random import Random

from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.node import Node
from randovania.game_description.game_database_view import GameDatabaseView
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.games.prime2.generator.base_patches_factory import SharedEchoesBasePatches
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.games.prime2_opr.layout import EchoesOPRConfiguration
from randovania.generator.base_patches_factory import BasePatchesFactory


class EchoesOPRBasePatchesFactory(BasePatchesFactory[EchoesOPRConfiguration]):
    def assign_static_dock_weakness(
        self, configuration: EchoesOPRConfiguration, game: GameDatabaseView, initial_patches: GamePatches
    ) -> GamePatches:
        parent = super().assign_static_dock_weakness(configuration, game, initial_patches)
        return SharedEchoesBasePatches.unlock_save_doors(configuration.blue_save_doors, game, parent)

    def dock_connections_assignment(
        self, configuration: EchoesOPRConfiguration, game: GameDatabaseView, rng: Random
    ) -> typing.Iterable[tuple[DockNode, Node]]:
        yield from super().dock_connections_assignment(configuration, game, rng)
        yield from SharedEchoesBasePatches.teleporter_assignment(configuration.teleporters, game, rng)

    def create_game_specific(self, configuration: EchoesConfiguration, game: GameDescription, rng: Random) -> dict:
        # TODO: turn translator gates into docks instead
        return {
            "translator_gates": SharedEchoesBasePatches.translator_gates(configuration.translator_configuration, rng),
        }
