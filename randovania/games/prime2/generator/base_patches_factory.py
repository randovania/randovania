import copy
import dataclasses
from collections.abc import Iterable
from random import Random

from randovania.game_description.assignment import NodeConfigurationAssociation
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches, ElevatorConnection
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources import search
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.configurable_node import ConfigurableNode
from randovania.game_description.world.dock_node import DockNode
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.games.prime2.layout.translator_configuration import LayoutTranslatorRequirement
from randovania.generator.base_patches_factory import (PrimeTrilogyBasePatchesFactory, MissingRng)


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
    def add_elevator_connections_to_patches(self, configuration: EchoesConfiguration, rng: Random,
                                            patches: GamePatches) -> GamePatches:
        patches = super().add_elevator_connections_to_patches(configuration, rng, patches)

        if not configuration.portal_rando:
            return patches

        dock_assignment = []

        for world in patches.game.world_list.worlds:
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
            area = patches.game.world_list.area_by_area_location(identifier)
            for node in area.actual_nodes:
                if node.valid_starting_location:
                    return node.identifier
            raise KeyError(f"{identifier} has no valid starting location")

        def link_to(source: AreaIdentifier, target: AreaIdentifier):
            result[area_to_node(source)] = target
            result[area_to_node(target)] = source

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

        for node in game.world_list.iterate_nodes():
            if not isinstance(node, ConfigurableNode):
                continue

            identifier = game.world_list.identifier_for_node(node)
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
