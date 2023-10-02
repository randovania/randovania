from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.db.pickup_node import PickupNode
from randovania.games.samus_returns.generator.pool_creator import METROID_DNA_CATEGORY
from randovania.games.samus_returns.layout.msr_configuration import MSRArtifactConfig, MSRConfiguration
from randovania.resolver.bootstrap import MetroidBootstrap

if TYPE_CHECKING:
    from random import Random

    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.game_description.resources.resource_info import ResourceGain
    from randovania.generator.pickup_pool import PoolResults
    from randovania.layout.base.base_configuration import BaseConfiguration


def all_dna_locations(game: GameDescription, config: MSRArtifactConfig):
    locations = []

    for node in game.region_list.all_nodes:
        if isinstance(node, PickupNode):
            # Metroid pickups
            pickup_type = node.extra.get("pickup_type")
            if config.prefer_metroids and pickup_type is not None and pickup_type == "metroid":
                locations.append(node)
            # DNA anywhere
            elif not config.prefer_metroids:
                locations.append(node)

    return locations


class MSRBootstrap(MetroidBootstrap):
    def _get_enabled_misc_resources(
        self, configuration: BaseConfiguration, resource_database: ResourceDatabase
    ) -> set[str]:
        enabled_resources = set()
        assert isinstance(configuration, MSRConfiguration)

        logical_patches = {
            "allow_highly_dangerous_logic": "HighDanger",
            "nerf_power_bombs": "NerfPBs",
            "nerf_super_missiles": "NerfSupers",
            "surface_crumbles": "SurfaceCrumbles",
            "area1_crumbles": "Area1Crumbles",
        }
        for name, index in logical_patches.items():
            if getattr(configuration, name):
                enabled_resources.add(index)

        return enabled_resources

    def event_resources_for_configuration(
        self,
        configuration: BaseConfiguration,
        resource_database: ResourceDatabase,
    ) -> ResourceGain:
        assert isinstance(configuration, MSRConfiguration)

        if configuration.elevator_grapple_blocks:
            for name in [
                "Area 4 (West) - Transport Area Grapple Block Pull Right",
                "Area 5 (Entrance) - Chozo Seal Grapple Block Bottom",
                "Area 6 - Transport to Area 7 Grapple Block Pull",
                "Area 7 - Transport to Area 8 Grapple Block",
            ]:
                yield resource_database.get_event(name), 1

        if configuration.area3_interior_shortcut_no_grapple:
            yield resource_database.get_event(
                "Area 3 (Interior East) - Transport to Area 3 Interior West Grapple Block"
            ), 1

    def assign_pool_results(self, rng: Random, patches: GamePatches, pool_results: PoolResults) -> GamePatches:
        assert isinstance(patches.configuration, MSRConfiguration)
        config = patches.configuration.artifacts

        locations = all_dna_locations(patches.game, config)
        rng.shuffle(locations)

        dna_to_assign = [
            pickup for pickup in list(pool_results.to_place) if pickup.pickup_category is METROID_DNA_CATEGORY
        ]

        for dna, location in zip(dna_to_assign, locations, strict=False):
            pool_results.to_place.remove(dna)
            pool_results.assignment[location.pickup_index] = dna

        return super().assign_pool_results(rng, patches, pool_results)
