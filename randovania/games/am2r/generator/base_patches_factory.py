from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.db.dock_node import DockNode
from randovania.games.am2r.layout.am2r_configuration import AM2RConfiguration
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
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.game_database_view import GameDatabaseView
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
    from randovania.layout.base.base_configuration import BaseConfiguration


class AM2RBasePatchesFactory(BasePatchesFactory):
    def create_base_patches(
        self,
        configuration: BaseConfiguration,
        rng: Random,
        game: GameDatabaseView,
        is_multiworld: bool,
        player_index: int,
    ) -> GamePatches:
        assert isinstance(configuration, AM2RConfiguration)
        parent = super().create_base_patches(configuration, rng, game, is_multiworld, player_index)

        dock_weakness: list[tuple[NodeIdentifier, DockWeakness]] = []
        door_type = [d for d in game.get_dock_types() if d.short_name == "door"][0]
        blue_door = game.get_dock_weakness("door", "Normal Door (Forced)")
        open_transition_door = game.get_dock_weakness("door", "Open Transition")
        are_transitions_shuffled = (
            open_transition_door in configuration.dock_rando.types_state[door_type].can_change_from
        )

        # TODO: separate these two into functions, so that they can be tested more easily?
        if configuration.blue_save_doors or configuration.force_blue_labs:
            for _, area, node in game.node_iterator():
                if (configuration.blue_save_doors and area.extra.get("unlocked_save_station")) or (
                    configuration.force_blue_labs and area.extra.get("force_blue_labs")
                ):
                    if isinstance(node, DockNode) and node.dock_type.short_name == "door":
                        if node.default_dock_weakness != open_transition_door or (
                            node.default_dock_weakness == open_transition_door and are_transitions_shuffled
                        ):
                            dock_weakness.append((node.identifier, blue_door))
                            # TODO: This is not correct in entrance rando
                            dock_weakness.append((node.default_connection, blue_door))

        return parent.assign_dock_weakness(dock_weakness)

    def dock_connections_assignment(
        self, configuration: BaseConfiguration, game: GameDescription, rng: Random
    ) -> Iterable[tuple[DockNode, Node]]:
        assert isinstance(configuration, AM2RConfiguration)
        teleporter_connection = get_teleporter_connections(
            configuration.teleporters, game, rng, [t for t in game.get_dock_types() if t.extra.get("is_teleporter")]
        )
        dock_assignment = get_dock_connections_assignment_for_teleporter(
            configuration.teleporters, game, teleporter_connection
        )
        yield from dock_assignment
