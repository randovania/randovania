from __future__ import annotations

import copy
import dataclasses
from typing import TYPE_CHECKING

from randovania.game_description.db.area_identifier import AreaIdentifier
from randovania.game_description.db.configurable_node import ConfigurableNode
from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources import search
from randovania.game_description.resources.resource_type import ResourceType
from randovania.games.prime2.layout.translator_configuration import LayoutTranslatorRequirement
from randovania.generator.base_patches_factory import MissingRng, PrimeTrilogyBasePatchesFactory

if TYPE_CHECKING:
    from collections.abc import Iterable
    from random import Random

    from randovania.game_description.assignment import NodeConfigurationAssociation
    from randovania.game_description.db.dock import DockWeakness
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import ElevatorConnection, GamePatches
    from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
    from randovania.layout.base.base_configuration import BaseConfiguration


@dataclasses.dataclass(frozen=True)
class WorldEntrances:
    front: AreaIdentifier
    left: AreaIdentifier
    right: AreaIdentifier

    @classmethod
    def create(cls, world, front, left, right):
        return cls(
            front=AreaIdentifier(world, front),
            left=AreaIdentifier(world, left),
            right=AreaIdentifier(world, right),
        )


WORLDS = [
    WorldEntrances.create(
        "Great Temple",
        front="Temple Transport A",  # Sanc
        left="Temple Transport B",  # Agon
        right="Temple Transport C",  # Torvus
    ),
    WorldEntrances.create(
        "Agon Wastes",
        front="Transport to Temple Grounds",
        left="Transport to Sanctuary Fortress",
        right="Transport to Torvus Bog",
    ),
    WorldEntrances.create(
        "Torvus Bog",
        front="Transport to Temple Grounds",
        left="Transport to Agon Wastes",
        right="Transport to Sanctuary Fortress",
    ),
    WorldEntrances.create(
        "Sanctuary Fortress",
        front="Transport to Temple Grounds",
        left="Transport to Torvus Bog",
        right="Transport to Agon Wastes",
    ),
]


class EchoesBasePatchesFactory(PrimeTrilogyBasePatchesFactory):
    def create_base_patches(self,
                            configuration: BaseConfiguration,
                            rng: Random,
                            game: GameDescription,
                            is_multiworld: bool,
                            player_index: int,
                            rng_required: bool = True) -> GamePatches:
        parent = super().create_base_patches(configuration, rng, game, is_multiworld, player_index, rng_required)
        return self.assign_save_door_weaknesses(parent, configuration, game)

    def add_elevator_connections_to_patches(self, configuration: EchoesConfiguration, rng: Random,
                                            patches: GamePatches) -> GamePatches:
        patches = super().add_elevator_connections_to_patches(configuration, rng, patches)

        if not configuration.portal_rando:
            return patches

        dock_assignment = []

        for world in patches.game.region_list.regions:
            light_portals = []
            dark_portals = []

            for area in world.areas:
                for node in area.nodes:
                    if isinstance(node, DockNode) and node.dock_type.short_name == "portal":
                        if area.in_dark_aether:
                            dark_portals.append(node)
                        else:
                            light_portals.append(node)

            assert len(light_portals) == len(dark_portals)
            rng.shuffle(light_portals)
            rng.shuffle(dark_portals)
            dock_assignment.extend(zip(light_portals, dark_portals))
            dock_assignment.extend(zip(dark_portals, light_portals))

        return patches.assign_dock_connections(dock_assignment)

    def elevator_echoes_shuffled(self, configuration: EchoesConfiguration, patches: GamePatches,
                                 rng: Random) -> ElevatorConnection:
        worlds = list(WORLDS)
        rng.shuffle(worlds)

        result = {}

        def area_to_node(identifier: AreaIdentifier):
            area = patches.game.region_list.area_by_area_location(identifier)
            for node in area.actual_nodes:
                if node.valid_starting_location:
                    return node.identifier
            raise KeyError(f"{identifier} has no valid starting location")

        def link_to(source: AreaIdentifier, target: AreaIdentifier):
            result[area_to_node(source)] = area_to_node(target)
            result[area_to_node(target)] = area_to_node(source)

        def tg_link_to(source: str, target: AreaIdentifier):
            link_to(AreaIdentifier("Temple Grounds", source), target)

        # TG -> GT
        tg_link_to("Temple Transport A", worlds[0].front)
        tg_link_to("Temple Transport B", worlds[0].left)
        tg_link_to("Temple Transport C", worlds[0].right)

        tg_link_to("Transport to Agon Wastes", worlds[1].front)
        tg_link_to("Transport to Torvus Bog", worlds[2].front)
        tg_link_to("Transport to Sanctuary Fortress", worlds[3].front)

        # inter areas
        link_to(worlds[1].right, worlds[2].left)
        link_to(worlds[2].right, worlds[3].left)
        link_to(worlds[3].right, worlds[1].left)

        return result

    def configurable_node_assignment(self, configuration: EchoesConfiguration, game: GameDescription,
                                     rng: Random) -> Iterable[NodeConfigurationAssociation]:
        """
        :param configuration:
        :param game:
        :param rng:
        :return:
        """

        all_choices = list(LayoutTranslatorRequirement)
        all_choices.remove(LayoutTranslatorRequirement.RANDOM)
        all_choices.remove(LayoutTranslatorRequirement.RANDOM_WITH_REMOVED)
        without_removed = copy.copy(all_choices)
        without_removed.remove(LayoutTranslatorRequirement.REMOVED)
        random_requirements = {LayoutTranslatorRequirement.RANDOM, LayoutTranslatorRequirement.RANDOM_WITH_REMOVED}

        result = []

        scan_visor = search.find_resource_info_with_long_name(
            game.resource_database.item,
            "Scan Visor"
        )
        scan_visor_req = ResourceRequirement.simple(scan_visor)

        for node in game.region_list.iterate_nodes():
            if not isinstance(node, ConfigurableNode):
                continue

            identifier = game.region_list.identifier_for_node(node)
            requirement = configuration.translator_configuration.translator_requirement[identifier]
            if requirement in random_requirements:
                if rng is None:
                    raise MissingRng("Translator")
                requirement = rng.choice(all_choices if requirement == LayoutTranslatorRequirement.RANDOM_WITH_REMOVED
                                         else without_removed)

            translator = game.resource_database.get_by_type_and_index(ResourceType.ITEM, requirement.item_name)
            result.append((identifier, RequirementAnd([
                scan_visor_req,
                ResourceRequirement.simple(translator),
            ])))

        return result

    def assign_save_door_weaknesses(self,
                                    patches: GamePatches,
                                    configuration: EchoesConfiguration,
                                    game: GameDescription) -> GamePatches:
        if not configuration.blue_save_doors:
            return patches

        get_node = game.region_list.typed_node_by_identifier
        power_weak = game.dock_weakness_database.get_by_weakness("door", "Normal Door (Forced)")
        dock_weakness: list[tuple[DockNode, DockWeakness]] = []

        if configuration.blue_save_doors:
            for area in game.region_list.all_areas:
                if area.extra.get("unlocked_save_station"):
                    for node in area.nodes:
                        if isinstance(node, DockNode) and node.dock_type.short_name == "door":
                            dock_weakness.append((node, power_weak))
                            # TODO: This is not correct in entrance rando
                            dock_weakness.append((get_node(node.default_connection, DockNode), power_weak))

        return patches.assign_dock_weakness(dock_weakness)
