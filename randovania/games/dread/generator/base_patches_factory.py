from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.games.dread.layout.dread_configuration import DreadConfiguration
from randovania.generator.base_patches_factory import BasePatchesFactory
from randovania.generator.teleporter_distributor import (
    get_dock_connections_assignment_for_teleporter,
    get_teleporter_connections,
)

if TYPE_CHECKING:
    from collections.abc import Iterable
    from random import Random

    from randovania.game_description.db.node import Node
    from randovania.game_description.game_database_view import GameDatabaseView
    from randovania.game_description.game_patches import GamePatches


class DreadBasePatchesFactory(BasePatchesFactory[DreadConfiguration]):
    def assign_static_dock_weakness(
        self, configuration: DreadConfiguration, game: GameDatabaseView, initial_patches: GamePatches
    ) -> GamePatches:
        parent = super().assign_static_dock_weakness(configuration, game, initial_patches)

        dock_weakness = []
        if configuration.hanubia_easier_path_to_itorash:
            nic = NodeIdentifier.create
            power_weak = game.get_dock_weakness("door", "Power Beam Door")

            dock_weakness.extend(
                [
                    (nic("Hanubia", "Entrance Tall Room", "Door to Total Recharge Station North"), power_weak),
                    (nic("Hanubia", "Total Recharge Station North", "Door to Gold Chozo Warrior Arena"), power_weak),
                ]
            )

        return parent.assign_dock_weakness(
            ((game.typed_node_by_identifier(identifier, DockNode), target) for identifier, target in dock_weakness)
        )

    def dock_connections_assignment(
        self, configuration: DreadConfiguration, game: GameDatabaseView, rng: Random
    ) -> Iterable[tuple[DockNode, Node]]:
        yield from super().dock_connections_assignment(configuration, game, rng)

        teleporter_connection = get_teleporter_connections(configuration.teleporters, game, rng)
        dock_assignment = get_dock_connections_assignment_for_teleporter(
            configuration.teleporters, game, teleporter_connection
        )
        yield from dock_assignment
