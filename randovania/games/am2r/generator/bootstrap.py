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
    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.game_description.resources.resource_database import ResourceDatabase
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
    def _get_enabled_misc_resources(
        self, configuration: BaseConfiguration, resource_database: ResourceDatabase
    ) -> set[str]:
        enabled_resources = set()

        logical_patches = {
            "septogg_helpers": "Septogg",
            "screw_blocks": "ScrewBlocks",
            "skip_cutscenes": "SkipCutscenes",
            "fusion_mode": "FusionMode",
            "softlock_prevention_blocks": "SoftlockPrevention",
            "respawn_bomb_blocks": "RespawnBombBlocks",
            "a3_entrance_blocks": "A3Entrance",
            "grave_grotto_blocks": "GraveGrottoBlocks",
            "supers_on_missile_doors": "SupersOnMissileDoors",
        }

        for name, index in logical_patches.items():
            if getattr(configuration, name):
                enabled_resources.add(index)

        if configuration.dock_rando.is_enabled():
            enabled_resources.add("DoorLockRando")

        return enabled_resources

    def _damage_reduction(self, db: ResourceDatabase, current_resources: ResourceCollection):
        num_suits = sum(current_resources[db.get_item_by_name(suit)] for suit in ["Varia Suit", "Gravity Suit"])
        return 2 ** (-num_suits)

    def patch_resource_database(self, db: ResourceDatabase, configuration: BaseConfiguration) -> ResourceDatabase:
        base_damage_reduction = self._damage_reduction

        return dataclasses.replace(db, base_damage_reduction=base_damage_reduction)

    def assign_pool_results(self, rng: Random, patches: GamePatches, pool_results: PoolResults) -> GamePatches:
        assert isinstance(patches.configuration, AM2RConfiguration)
        config = patches.configuration.artifacts

        if config.prefer_anywhere:
            return super().assign_pool_results(rng, patches, pool_results)

        locations = all_dna_locations(patches.game, config)
        rng.shuffle(locations)

        dna_to_assign = [
            pickup for pickup in list(pool_results.to_place) if pickup.pickup_category is METROID_DNA_CATEGORY
        ]

        if len(dna_to_assign) > len(locations):
            raise InvalidConfiguration(
                f"Has {len(dna_to_assign)} DNA in the pool, but only {len(locations)} valid locations."
            )

        for dna, location in zip(dna_to_assign, locations, strict=False):
            pool_results.to_place.remove(dna)
            pool_results.assignment[location.pickup_index] = dna

        return super().assign_pool_results(rng, patches, pool_results)


_boss_items = ["oItemM_111", "oItemJumpBall", "oItemSpaceJump", "oItemPBeam", "oItemIBeam", "oItemETank_50"]
