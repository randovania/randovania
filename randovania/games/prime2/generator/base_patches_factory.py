from __future__ import annotations

import copy
import dataclasses
from typing import TYPE_CHECKING

from randovania.game_description.db.area_identifier import AreaIdentifier
from randovania.game_description.db.dock_node import DockNode
from randovania.games.prime2.generator.teleporter_distributor import get_teleporter_connections_echoes
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.games.prime2.layout.translator_configuration import LayoutTranslatorRequirement
from randovania.generator.base_patches_factory import BasePatchesFactory, MissingRng
from randovania.generator.teleporter_distributor import get_dock_connections_assignment_for_teleporter

if TYPE_CHECKING:
    from collections.abc import Iterable
    from random import Random

    from randovania.game_description.db.dock import DockWeakness
    from randovania.game_description.db.node import Node
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
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


class EchoesBasePatchesFactory(BasePatchesFactory):
    def create_base_patches(
        self,
        configuration: BaseConfiguration,
        rng: Random,
        game: GameDescription,
        is_multiworld: bool,
        player_index: int,
        rng_required: bool = True,
    ) -> GamePatches:
        assert isinstance(configuration, EchoesConfiguration)
        parent = super().create_base_patches(configuration, rng, game, is_multiworld, player_index, rng_required)
        return self.assign_save_door_weaknesses(parent, configuration, game)

    def dock_connections_assignment(
        self, configuration: EchoesConfiguration, game: GameDescription, rng: Random
    ) -> Iterable[tuple[DockNode, Node]]:
        teleporter_connection = get_teleporter_connections_echoes(configuration.teleporters, game, rng)
        dock_assignment = get_dock_connections_assignment_for_teleporter(
            configuration.teleporters, game, teleporter_connection
        )

        if not configuration.portal_rando:
            yield from dock_assignment
            return

        for world in game.region_list.regions:
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

    def assign_save_door_weaknesses(
        self, patches: GamePatches, configuration: EchoesConfiguration, game: GameDescription
    ) -> GamePatches:
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
