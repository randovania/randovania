from random import Random
from typing import Iterator

from randovania.game_description.assignment import NodeConfigurationAssociation
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.world.configurable_node import ConfigurableNode
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.games.dread.layout.dread_configuration import DreadConfiguration
from randovania.generator.base_patches_factory import PrimeTrilogyBasePatchesFactory
from randovania.layout.base.base_configuration import BaseConfiguration


class DreadBasePatchesFactory(PrimeTrilogyBasePatchesFactory):
    @property
    def num_joke_hints(self) -> int:
        return 0

    def configurable_node_assignment(self, configuration: DreadConfiguration, game: GameDescription,
                                     rng: Random) -> Iterator[NodeConfigurationAssociation]:
        result = []

        rsb = game.resource_database

        requirement_for_type = {
            "POWERBEAM": rsb.requirement_template["Shoot Beam"],
            "BOMB": rsb.requirement_template["Lay Bomb"],
            "MISSILE": rsb.requirement_template["Shoot Missile"],
            "SUPERMISSILE": rsb.requirement_template["Shoot Super Missile"],
            "POWERBOMB": rsb.requirement_template["Lay Power Bomb"],
            "SCREWATTACK": ResourceRequirement.simple(rsb.get_item("Screw")),
            "WEIGHT": Requirement.impossible(),
            "SPEEDBOOST": ResourceRequirement.simple(rsb.get_item("Speed")),
        }

        for node in game.world_list.iterate_nodes():
            if not isinstance(node, ConfigurableNode):
                continue

            result.append((game.world_list.identifier_for_node(node), RequirementAnd([
                requirement_for_type[block_type]
                for block_type in node.extra["tile_types"]
            ]).simplify()))

        return result

    def create_base_patches(self,
                            configuration: BaseConfiguration,
                            rng: Random,
                            game: GameDescription,
                            is_multiworld: bool,
                            player_index: int,
                            rng_required: bool = True
                            ) -> GamePatches:
        assert isinstance(configuration, DreadConfiguration)
        parent = super().create_base_patches(configuration, rng, game, is_multiworld, player_index, rng_required)

        dock_weakness = []
        if configuration.hanubia_easier_path_to_itorash:
            nic = NodeIdentifier.create
            power_weak = game.dock_weakness_database.get_by_weakness("door", "Power Beam Door")

            dock_weakness.extend([
                (nic("Hanubia", "Entrance Tall Room", "Door to Total Recharge Station North"), power_weak),
                (nic("Hanubia", "Total Recharge Station North", "Door to Gold Chozo Warrior Arena"), power_weak),
            ])

        return parent.assign_dock_weakness((
            (game.world_list.node_by_identifier(identifier), target)
            for identifier, target in dock_weakness
        ))
