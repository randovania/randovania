from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.db.pickup_node import PickupNode
from randovania.games.fusion.generator.pool_creator import INFANT_METROID_CATEGORY
from randovania.games.fusion.layout import FusionConfiguration
from randovania.layout.exceptions import InvalidConfiguration
from randovania.resolver.bootstrap import MetroidBootstrap

if TYPE_CHECKING:
    from random import Random

    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.games.fusion.layout.fusion_configuration import FusionArtifactConfig
    from randovania.generator.pickup_pool import PoolResults
    from randovania.layout.base.base_configuration import BaseConfiguration


def all_metroid_locations(game: GameDescription, config: FusionArtifactConfig) -> list[PickupNode]:
    locations = []
    for node in game.region_list.all_nodes:
        if isinstance(node, PickupNode):
            index = node.pickup_index.index
            # Pickups guarded by bosses
            if config.prefer_bosses and index in _boss_indices:
                locations.append(node)

    return locations


class FusionBootstrap(MetroidBootstrap):
    def _get_enabled_misc_resources(
        self, configuration: BaseConfiguration, resource_database: ResourceDatabase
    ) -> set[str]:
        enabled_resources = set()
        if configuration.dock_rando.is_enabled():
            enabled_resources.add("DoorLockRando")
        return enabled_resources

    def assign_pool_results(self, rng: Random, patches: GamePatches, pool_results: PoolResults) -> GamePatches:
        assert isinstance(patches.configuration, FusionConfiguration)
        config = patches.configuration.artifacts

        if config.prefer_anywhere:
            return super().assign_pool_results(rng, patches, pool_results)

        locations = all_metroid_locations(patches.game, config)
        rng.shuffle(locations)

        metroid_to_assign = [
            pickup for pickup in list(pool_results.to_place) if pickup.pickup_category is INFANT_METROID_CATEGORY
        ]

        if len(metroid_to_assign) > len(locations):
            raise InvalidConfiguration(
                f"Has {len(metroid_to_assign)} Infant Metroids in the pool, but only {len(locations)} valid locations."
            )

        for metroid, location in zip(metroid_to_assign, locations, strict=False):
            pool_results.to_place.remove(metroid)
            pool_results.assignment[location.pickup_index] = metroid

        return super().assign_pool_results(rng, patches, pool_results)


_boss_indices = [100, 106, 114, 104, 115, 107, 110, 102, 109, 108, 111]
