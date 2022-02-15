from random import Random

from randovania.game_description.assignment import NodeConfigurationAssignment
from randovania.game_description.game_description import GameDescription
from randovania.game_description.requirements import (
    Requirement,
    RequirementAnd,
    ResourceRequirement,
)
from randovania.game_description.world.node import ConfigurableNode
from randovania.games.dread.layout.dread_configuration import DreadConfiguration
from randovania.generator.base_patches_factory import PrimeTrilogyBasePatchesFactory


class DreadBasePatchesFactory(PrimeTrilogyBasePatchesFactory):
    @property
    def num_joke_hints(self) -> int:
        return 0

    def configurable_node_assignment(self, configuration: DreadConfiguration, game: GameDescription,
                                     rng: Random) -> NodeConfigurationAssignment:
        result = {}

        rsb = game.resource_database

        requirement_for_type = {
            "POWERBEAM": rsb.requirement_template["Shoot Beam"],
            "BOMB": rsb.requirement_template["Lay Bomb"],
            "MISSILE": rsb.requirement_template["Shoot Missile"],
            "SUPERMISSILE": rsb.requirement_template["Shoot Super Missile"],
            "POWERBOMB": rsb.requirement_template["Lay Power Bomb"],
            "SCREWATTACK": ResourceRequirement(rsb.get_item("Screw"), 1, False),
            "WEIGHT": Requirement.impossible(),
            "SPEEDBOOST": ResourceRequirement(rsb.get_item("Speed"), 1, False),
        }

        for node in game.world_list.all_nodes:
            if not isinstance(node, ConfigurableNode):
                continue

            result[game.world_list.identifier_for_node(node)] = RequirementAnd([
                requirement_for_type[block_type]
                for block_type in node.extra["tile_types"]
            ]).simplify()

        return result
