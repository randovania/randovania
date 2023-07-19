from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.game_description.db.pickup_node import PickupNode
from randovania.games.am2r.generator.pool_creator import METROID_DNA_CATEGORY
from randovania.games.am2r.layout import AM2RConfiguration
from randovania.layout.exceptions import InvalidConfiguration
from randovania.resolver.bootstrap import MetroidBootstrap

if TYPE_CHECKING:
    from random import Random

    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.game_description.resources.resource_info import ResourceCollection
    from randovania.games.am2r.layout.am2r_configuration import AM2RArtifactConfig
    from randovania.generator.pickup_pool import PoolResults
    from randovania.layout.base.base_configuration import BaseConfiguration


def all_dna_locations(game: GameDescription, config: AM2RArtifactConfig):
    locations = []

    for node in game.region_list.all_nodes:
        if isinstance(node, PickupNode):
            # Metroid pickups
            name = node.extra["object_name"]
            if config.prefer_metroids and name.startswith("oItemDNA_"):
                locations.append(node)
            # Pickups guarded by bosses
            elif config.prefer_bosses and name in _boss_items:
                locations.append(node)

    return locations


class AM2RBootstrap(MetroidBootstrap):
    def _get_enabled_misc_resources(self, configuration: BaseConfiguration,
                                    resource_database: ResourceDatabase) -> set[str]:

        enabled_resources = set()

        logical_patches = {
            "septogg_helpers": "Septogg",
            "screw_blocks": "ScrewBlocks",
            "skip_cutscenes": "SkipCutscenes",
            "respawn_bomb_blocks": "RespawnBombBlocks",
            "a3_entrance_blocks": "A3Entrance",
            "grave_grotto_blocks": "GraveGrottoBlocks"
        }

        for name, index in logical_patches.items():
            if getattr(configuration, name):
                enabled_resources.add(index)

        return enabled_resources

    def _damage_reduction(self, db: ResourceDatabase, current_resources: ResourceCollection):
        num_suits = sum(current_resources[db.get_item_by_name(suit)]
                        for suit in ["Varia Suit", "Gravity Suit"])
        return 2 ** (-num_suits)

    def patch_resource_database(self, db: ResourceDatabase, configuration: BaseConfiguration) -> ResourceDatabase:
        base_damage_reduction = self._damage_reduction

        return dataclasses.replace(db, base_damage_reduction=base_damage_reduction)

    def assign_pool_results(self, rng: Random, patches: GamePatches, pool_results: PoolResults) -> GamePatches:
        assert isinstance(patches.configuration, AM2RConfiguration)
        config = patches.configuration.artifacts

        locations = all_dna_locations(patches.game, config)
        rng.shuffle(locations)

        total_dna = [pickup for pickup in pool_results.to_place + pool_results.starting
                     if pickup.pickup_category is METROID_DNA_CATEGORY]

        num_of_dna = sum(1 for pickup in pool_results.to_place if pickup.pickup_category is METROID_DNA_CATEGORY)
        if num_of_dna > len(locations):
            raise InvalidConfiguration(
                f"Has {num_of_dna} DNA in the pool, but only {len(locations)} valid locations."
            )

        # Shuffle DNA, so that it isn't always just the first X DNA
        # For this, get all DNA, remove them from starting/place, shuffle them, then add the new ones back
        rng.shuffle(total_dna)

        temp_to_place = [p for p in pool_results.to_place if p.pickup_category is not METROID_DNA_CATEGORY]
        pool_results.to_place.clear()
        pool_results.to_place.extend(temp_to_place)

        temp_start = [p for p in pool_results.starting if p.pickup_category is not METROID_DNA_CATEGORY]
        pool_results.starting.clear()
        pool_results.starting.extend(temp_start)

        dna_to_place = total_dna[:num_of_dna]
        pool_results.to_place.extend(dna_to_place)
        pool_results.starting.extend(total_dna[len(dna_to_place):])

        for dna, location in zip(dna_to_place, locations, strict=False):
            pool_results.to_place.remove(dna)
            pool_results.assignment[location.pickup_index] = dna

        return super().assign_pool_results(rng, patches, pool_results)


_boss_items = [
    "oItemM_111",
    "oItemJumpBall",
    "oItemSpaceJump",
    "oItemPBeam",
    "oItemIBeam",
    "oItemETank_50"
]
