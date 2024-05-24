from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.fusion.generator.pool_creator import INFANT_METROID_CATEGORY
from randovania.games.fusion.layout import FusionConfiguration
from randovania.resolver.bootstrap import MetroidBootstrap

if TYPE_CHECKING:
    from random import Random

    from randovania.game_description.db.pickup_node import PickupNode
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.generator.pickup_pool import PoolResults
    from randovania.layout.base.base_configuration import BaseConfiguration


def is_metroid_location(node: PickupNode, config: BaseConfiguration) -> bool:
    assert isinstance(config, FusionConfiguration)
    _boss_indices = [100, 106, 114, 104, 115, 107, 110, 102, 109, 108, 111]
    artifact_config = config.artifacts
    index = node.pickup_index.index
    return artifact_config.prefer_bosses and index in _boss_indices


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

        locations = self.all_preplaced_item_locations(patches.game, patches.configuration, is_metroid_location)
        self.pre_place_items(rng, locations, pool_results, INFANT_METROID_CATEGORY)
        return super().assign_pool_results(rng, patches, pool_results)
