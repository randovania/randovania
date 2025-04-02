from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.games.prime1.layout.prime_configuration import PrimeConfiguration
from randovania.generator.base_patches_factory import BasePatchesFactory, weaknesses_for_unlocked_saves
from randovania.generator.teleporter_distributor import (
    get_dock_connections_assignment_for_teleporter,
    get_teleporter_connections,
)

if TYPE_CHECKING:
    from collections.abc import Iterable
    from random import Random

    from randovania.game_description.db.dock import DockWeakness
    from randovania.game_description.db.node import Node
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches


class PrimeBasePatchesFactory(BasePatchesFactory[PrimeConfiguration]):
    def assign_static_dock_weakness(
        self, configuration: PrimeConfiguration, game: GameDescription, initial_patches: GamePatches
    ) -> GamePatches:
        parent = super().assign_static_dock_weakness(configuration, game, initial_patches)

        nic = NodeIdentifier.create
        get_node = game.region_list.typed_node_by_identifier

        dock_weakness: list[tuple[DockNode, DockWeakness]] = []
        power_weak = game.dock_weakness_database.get_by_weakness("door", "Normal Door (Forced)")

        if configuration.main_plaza_door and not configuration.dock_rando.is_enabled():
            dock_weakness.append(
                (get_node(nic("Chozo Ruins", "Main Plaza", "Door from Plaza Access"), DockNode), power_weak),
            )

        if configuration.blue_save_doors:
            dock_weakness.extend(
                weaknesses_for_unlocked_saves(
                    game,
                    unlocked_weakness=power_weak,
                    target_dock_type=game.dock_weakness_database.find_type("door"),
                    area_filter=lambda area: area.extra.get("unlocked_save_station") is True,
                )
            )

        return parent.assign_dock_weakness(dock_weakness)

    def dock_connections_assignment(
        self, configuration: PrimeConfiguration, game: GameDescription, rng: Random
    ) -> Iterable[tuple[DockNode, Node]]:
        teleporter_connection = get_teleporter_connections(configuration.teleporters, game, rng)
        dock_assignment = get_dock_connections_assignment_for_teleporter(
            configuration.teleporters, game, teleporter_connection
        )
        yield from dock_assignment
