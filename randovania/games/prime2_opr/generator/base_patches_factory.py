from __future__ import annotations

import collections
import typing
from random import Random

from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.node import Node
from randovania.game_description.game_database_view import GameDatabaseView
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.games.prime2 import dark_aether_helper
from randovania.games.prime2.generator.base_patches_factory import SharedEchoesBasePatches
from randovania.games.prime2_opr.layout import EchoesOPRConfiguration
from randovania.generator.base_patches_factory import BasePatchesFactory


class EchoesOPRBasePatchesFactory(BasePatchesFactory[EchoesOPRConfiguration]):
    def assign_static_dock_weakness(
        self, configuration: EchoesOPRConfiguration, game: GameDatabaseView, initial_patches: GamePatches
    ) -> GamePatches:
        parent = super().assign_static_dock_weakness(configuration, game, initial_patches)

        if configuration.portal_rando:
            portal_type = game.find_dock_type_by_short_name("portal")
            light_portal = game.get_dock_weakness("portal", "Light Portal")
            dark_portal = game.get_dock_weakness("portal", "Dark Portal")

            static_portals = []
            for region, area, node in game.iterate_nodes_of_type(DockNode):
                if node.dock_type == portal_type and node.default_dock_weakness.name == "No Return Portal":
                    static_portals.append(
                        (node, dark_portal if dark_aether_helper.is_region_light(region) else light_portal)
                    )
            parent = parent.assign_dock_weakness(static_portals)

        return SharedEchoesBasePatches.unlock_save_doors(configuration.blue_save_doors, game, parent)

    def dock_connections_assignment(
        self, configuration: EchoesOPRConfiguration, game: GameDatabaseView, rng: Random
    ) -> typing.Iterable[tuple[DockNode, Node]]:
        yield from super().dock_connections_assignment(configuration, game, rng)
        yield from SharedEchoesBasePatches.teleporter_assignment(configuration.teleporters, game, rng)
        if configuration.portal_rando:
            yield from self.portal_assignment(game, rng)

    def portal_assignment(self, game: GameDatabaseView, rng: Random) -> typing.Iterable[tuple[DockNode, Node]]:
        light_portals_by_region: dict[str, list[DockNode]] = collections.defaultdict(list)
        dark_portals_by_region: dict[str, list[DockNode]] = collections.defaultdict(list)
        portal_type = game.find_dock_type_by_short_name("portal")

        for region, area, node in game.iterate_nodes_of_type(DockNode):
            if node.dock_type == portal_type:
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
            yield from zip(light_portals, dark_portals, strict=True)
            yield from zip(dark_portals, light_portals, strict=True)

    def create_game_specific(self, configuration: EchoesOPRConfiguration, game: GameDescription, rng: Random) -> dict:
        # TODO: turn translator gates into docks instead
        return {
            "translator_gates": SharedEchoesBasePatches.translator_gates(configuration.translator_configuration, rng),
        }
