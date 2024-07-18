from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.db.dock_node import DockNode
from randovania.games.am2r.layout.am2r_configuration import AM2RConfiguration
from randovania.generator.base_patches_factory import BasePatchesFactory
from randovania.generator.teleporter_distributor import (
    TeleporterHelper,
    get_dock_connections_assignment_for_teleporter,
    get_teleporter_connections_for_db,
)

if TYPE_CHECKING:
    from collections.abc import Iterable
    from random import Random

    from randovania.game_description.db.dock import DockType, DockWeakness
    from randovania.game_description.db.node import Node
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.db.region_list import RegionList
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
        teleporter_connection = get_teleporter_connections_for_db(
            configuration.teleporters,
            game,
            rng,
            create_pipe_rando_database(
                game.region_list,
                configuration.teleporters.editable_teleporters,
                game.dock_weakness_database.all_teleporter_dock_types,
            ),
        )
        area_connections = get_teleporter_connections_for_db(
            configuration.areas,
            game,
            rng,
            create_area_rando_database(
                game.region_list,
                configuration.areas.editable_teleporters,
                game.dock_weakness_database.all_teleporter_dock_types,
            ),
        )
        foo = get_dock_connections_assignment_for_teleporter(configuration.teleporters, game, teleporter_connection)
        bar = get_dock_connections_assignment_for_teleporter(configuration.areas, game, area_connections)
        dock_assignment = foo + bar
        yield from dock_assignment


def create_area_rando_database(
    region_list: RegionList, all_teleporters: list[NodeIdentifier], allowed_dock_types: list[DockType]
) -> tuple[TeleporterHelper, ...]:
    """
    Creates a tuple of Teleporter objects for area rando, exclude those that belongs to one of the areas provided.
    :param region_list:
    :param all_teleporters: Set of teleporters to use
    :return:
    """
    all_helpers = [
        TeleporterHelper(node.identifier, node.default_connection)
        for region, area, node in region_list.all_regions_areas_nodes
        if isinstance(node, DockNode)
        and node.dock_type in allowed_dock_types
        and node.extra.get("is_area_transition", False)
    ]
    return tuple(helper for helper in all_helpers if helper.teleporter in all_teleporters)


def create_pipe_rando_database(
    region_list: RegionList, all_teleporters: list[NodeIdentifier], allowed_dock_types: list[DockType]
) -> tuple[TeleporterHelper, ...]:
    """
    Creates a tuple of Teleporter objects for pipe rando, exclude those that belongs to one of the areas provided.
    :param region_list:
    :param all_teleporters: Set of teleporters to use
    :return:
    """
    all_helpers = [
        TeleporterHelper(node.identifier, node.default_connection)
        for region, area, node in region_list.all_regions_areas_nodes
        if isinstance(node, DockNode)
        and node.dock_type in allowed_dock_types
        and node.dock_type.short_name == "teleporter"
    ]
    return tuple(helper for helper in all_helpers if helper.teleporter in all_teleporters)
