from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.db.configurable_node import ConfigurableNode
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.games.dread.layout.dread_configuration import DreadConfiguration
from randovania.generator.base_patches_factory import BasePatchesFactory
from randovania.generator.teleporter_distributor import (
    get_dock_connections_assignment_for_teleporter,
    get_teleporter_connections,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from random import Random

    from randovania.game_description.assignment import NodeConfigurationAssociation
    from randovania.game_description.db.dock_node import DockNode
    from randovania.game_description.db.node import Node
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
    from randovania.layout.base.base_configuration import BaseConfiguration


class DreadBasePatchesFactory(BasePatchesFactory):
    def configurable_node_assignment(
        self, configuration: DreadConfiguration, game: GameDescription, rng: Random
    ) -> Iterator[NodeConfigurationAssociation]:
        result = []

        rsb = game.resource_database

        requirement_for_type = {
            "POWERBEAM": rsb.requirement_template["Shoot Beam"].requirement,
            "BOMB": rsb.requirement_template["Lay Bomb"].requirement,
            "MISSILE": rsb.requirement_template["Shoot Missile"].requirement,
            "SUPERMISSILE": rsb.requirement_template["Shoot Super Missile"].requirement,
            "POWERBOMB": rsb.requirement_template["Lay Power Bomb"].requirement,
            "SCREWATTACK": ResourceRequirement.simple(rsb.get_item("Screw")),
            "WEIGHT": Requirement.impossible(),
            "SPEEDBOOST": ResourceRequirement.simple(rsb.get_item("Speed")),
        }

        for node in game.region_list.iterate_nodes():
            if not isinstance(node, ConfigurableNode):
                continue

            result.append(
                (
                    game.region_list.identifier_for_node(node),
                    RequirementAnd(
                        [requirement_for_type[block_type] for block_type in node.extra["tile_types"]]
                    ).simplify(),
                )
            )

        return result

    def create_base_patches(
        self,
        configuration: BaseConfiguration,
        rng: Random,
        game: GameDescription,
        is_multiworld: bool,
        player_index: int,
        rng_required: bool = True,
    ) -> GamePatches:
        assert isinstance(configuration, DreadConfiguration)
        parent = super().create_base_patches(configuration, rng, game, is_multiworld, player_index, rng_required)

        dock_weakness = []
        if configuration.hanubia_easier_path_to_itorash:
            nic = NodeIdentifier.create
            power_weak = game.dock_weakness_database.get_by_weakness("door", "Power Beam Door")

            dock_weakness.extend(
                [
                    (nic("Hanubia", "Entrance Tall Room", "Door to Total Recharge Station North"), power_weak),
                    (nic("Hanubia", "Total Recharge Station North", "Door to Gold Chozo Warrior Arena"), power_weak),
                ]
            )

        return parent.assign_dock_weakness(
            ((game.region_list.node_by_identifier(identifier), target) for identifier, target in dock_weakness)
        )

    def dock_connections_assignment(
        self, configuration: DreadConfiguration, game: GameDescription, rng: Random
    ) -> Iterable[tuple[DockNode, Node]]:
        teleporter_connection = get_teleporter_connections(configuration.teleporters, game, rng)
        dock_assignment = get_dock_connections_assignment_for_teleporter(
            configuration.teleporters, game, teleporter_connection
        )
        yield from dock_assignment
