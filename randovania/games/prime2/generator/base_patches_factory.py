from __future__ import annotations

import collections
import copy
import dataclasses
from typing import TYPE_CHECKING, Self

from randovania.game_description.db.area_identifier import AreaIdentifier
from randovania.game_description.db.dock_node import DockNode
from randovania.games.prime2 import dark_aether_helper
from randovania.games.prime2.generator.teleporter_distributor import get_teleporter_connections_echoes
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.games.prime2.layout.translator_configuration import LayoutTranslatorRequirement
from randovania.generator.base_patches_factory import BasePatchesFactory, MissingRng, weaknesses_for_unlocked_saves
from randovania.generator.teleporter_distributor import get_dock_connections_assignment_for_teleporter

if TYPE_CHECKING:
    from collections.abc import Iterable
    from random import Random

    from randovania.game_description.db.dock import DockWeakness
    from randovania.game_description.db.node import Node
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches


@dataclasses.dataclass(frozen=True)
class WorldEntrances:
    front: AreaIdentifier
    left: AreaIdentifier
    right: AreaIdentifier

    @classmethod
    def create(cls, world: str, front: str, left: str, right: str) -> Self:
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


class EchoesBasePatchesFactory(BasePatchesFactory[EchoesConfiguration]):
    def assign_static_dock_weakness(
        self, configuration: EchoesConfiguration, game: GameDescription, initial_patches: GamePatches
    ) -> GamePatches:
        parent = super().assign_static_dock_weakness(configuration, game, initial_patches)

        dock_weakness: list[tuple[DockNode, DockWeakness]] = []

        if configuration.blue_save_doors:
            dock_weakness.extend(
                weaknesses_for_unlocked_saves(
                    game,
                    unlocked_weakness=game.dock_weakness_database.get_by_weakness("door", "Normal Door (Forced)"),
                    target_dock_type=game.dock_weakness_database.find_type("door"),
                    area_filter=lambda area: area.extra.get("unlocked_save_station") is True,
                )
            )

        return parent.assign_dock_weakness(dock_weakness)

    def dock_connections_assignment(
        self, configuration: EchoesConfiguration, game: GameDescription, rng: Random
    ) -> Iterable[tuple[DockNode, Node]]:
        teleporter_connection = get_teleporter_connections_echoes(configuration.teleporters, game, rng)
        dock_assignment = get_dock_connections_assignment_for_teleporter(
            configuration.teleporters, game, teleporter_connection
        )

        if configuration.portal_rando:
            light_portals_by_region: dict[str, list[DockNode]] = collections.defaultdict(list)
            dark_portals_by_region: dict[str, list[DockNode]] = collections.defaultdict(list)

            for region, area, node in game.region_list.all_regions_areas_nodes:
                if isinstance(node, DockNode) and node.dock_type.short_name == "portal":
                    if dark_aether_helper.is_region_light(region):
                        portal_list = light_portals_by_region[region.name]
                    else:
                        portal_list = dark_portals_by_region[dark_aether_helper.get_counterpart_name(region)]
                    portal_list.append(node)

            for region_name, light_portals in light_portals_by_region.items():
                dark_portals = dark_portals_by_region[region_name]
                assert len(light_portals) == len(dark_portals)
                rng.shuffle(light_portals)
                rng.shuffle(dark_portals)
                dock_assignment.extend(zip(light_portals, dark_portals))
                dock_assignment.extend(zip(dark_portals, light_portals))

        yield from dock_assignment

    def create_game_specific(self, configuration: EchoesConfiguration, game: GameDescription, rng: Random) -> dict:
        all_choices = list(LayoutTranslatorRequirement)
        all_choices.remove(LayoutTranslatorRequirement.RANDOM)
        all_choices.remove(LayoutTranslatorRequirement.RANDOM_WITH_REMOVED)
        without_removed = copy.copy(all_choices)
        without_removed.remove(LayoutTranslatorRequirement.REMOVED)
        random_requirements = {LayoutTranslatorRequirement.RANDOM, LayoutTranslatorRequirement.RANDOM_WITH_REMOVED}

        translator_gates = {}

        for identifier, requirement in configuration.translator_configuration.translator_requirement.items():
            if requirement in random_requirements:
                if rng is None:
                    raise MissingRng("Translator")

                requirement = rng.choice(
                    all_choices if requirement == LayoutTranslatorRequirement.RANDOM_WITH_REMOVED else without_removed
                )

            translator_gates[identifier.as_string] = requirement.value

        return {
            "translator_gates": translator_gates,
        }
