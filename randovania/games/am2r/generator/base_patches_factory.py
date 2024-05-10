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
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
    from randovania.layout.base.base_configuration import BaseConfiguration


class AM2RBasePatchesFactory(BasePatchesFactory):
    def create_base_patches(
        self,
        configuration: BaseConfiguration,
        rng: Random,
        game: GameDescription,
        is_multiworld: bool,
        player_index: int,
        rng_required: bool = True,
    ) -> GamePatches:
        assert isinstance(configuration, AM2RConfiguration)
        parent = super().create_base_patches(configuration, rng, game, is_multiworld, player_index, rng_required)

        get_node = game.region_list.typed_node_by_identifier

        dock_weakness: list[tuple[DockNode, DockWeakness]] = []
        blue_door = game.dock_weakness_database.get_by_weakness("door", "Normal Door (Forced)")
        door_type = game.dock_weakness_database.find_type("door")
        open_transition_door = game.dock_weakness_database.get_by_weakness("door", "Open Transition")
        are_transitions_shuffled = (
            open_transition_door in configuration.dock_rando.types_state[door_type].can_change_from
        )

        # TODO: separate these two into functions, so that they can be tested more easily?
        if configuration.blue_save_doors or configuration.force_blue_labs:
            for area in game.region_list.all_areas:
                if (configuration.blue_save_doors and area.extra.get("unlocked_save_station")) or (
                    configuration.force_blue_labs and area.extra.get("force_blue_labs")
                ):
                    for node in area.nodes:
                        if isinstance(node, DockNode) and node.dock_type.short_name == "door":
                            if node.default_dock_weakness != open_transition_door or (
                                node.default_dock_weakness == open_transition_door and are_transitions_shuffled
                            ):
                                dock_weakness.append((node, blue_door))
                                # TODO: This is not correct in entrance rando
                                dock_weakness.append((get_node(node.default_connection, DockNode), blue_door))

        return parent.assign_dock_weakness(dock_weakness)

    def dock_connections_assignment(
        self, configuration: BaseConfiguration, game: GameDescription, rng: Random
    ) -> Iterable[tuple[DockNode, Node]]:
        assert isinstance(configuration, AM2RConfiguration)
        teleporter_connection = get_teleporter_connections(configuration.teleporters, game, rng)
        dock_assignment = get_dock_connections_assignment_for_teleporter(
            configuration.teleporters, game, teleporter_connection
        )
        yield from dock_assignment
