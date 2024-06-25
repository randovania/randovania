from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.games.prime1.layout.prime_configuration import PrimeConfiguration
from randovania.generator.base_patches_factory import BasePatchesFactory
from randovania.generator.teleporter_distributor import (
    get_dock_connections_assignment_for_teleporter,
    get_teleporter_connections,
)

if TYPE_CHECKING:
    from collections.abc import Iterable
    from random import Random

    from randovania.game_description.db.dock import DockWeakness
    from randovania.game_description.db.node import Node
    from randovania.game_description.game_database_view import GameDatabaseView
    from randovania.game_description.game_patches import GamePatches
    from randovania.layout.base.base_configuration import BaseConfiguration


class PrimeBasePatchesFactory(BasePatchesFactory):
    def create_base_patches(
        self,
        configuration: BaseConfiguration,
        rng: Random,
        game: GameDatabaseView,
        is_multiworld: bool,
        player_index: int,
    ) -> GamePatches:
        assert isinstance(configuration, PrimeConfiguration)
        parent = super().create_base_patches(configuration, rng, game, is_multiworld, player_index)

        nic = NodeIdentifier.create

        dock_weakness: list[tuple[NodeIdentifier, DockWeakness]] = []
        power_weak = game.get_dock_weakness("door", "Normal Door (Forced)")

        if configuration.main_plaza_door and not configuration.dock_rando.is_enabled():
            dock_weakness.append(
                (nic("Chozo Ruins", "Main Plaza", "Door from Plaza Access"), power_weak),
            )

        if configuration.blue_save_doors:
            for _, area, node in game.node_iterator():
                if (
                    area.extra.get("unlocked_save_station")
                    and isinstance(node, DockNode)
                    and node.dock_type.short_name == "door"
                ):
                    dock_weakness.append((node.identifier, power_weak))
                    # TODO: This is not correct in entrance rando
                    dock_weakness.append((node.default_connection, power_weak))

        return parent.assign_dock_weakness(dock_weakness)

    def dock_connections_assignment(
        self, configuration: PrimeConfiguration, game: GameDatabaseView, rng: Random
    ) -> Iterable[tuple[DockNode, Node]]:
        teleporter_connection = get_teleporter_connections(
            configuration.teleporters, game, rng, [t for t in game.get_dock_types() if t.extra.get("is_teleporter")]
        )
        dock_assignment = get_dock_connections_assignment_for_teleporter(
            configuration.teleporters, game, teleporter_connection
        )
        yield from dock_assignment
