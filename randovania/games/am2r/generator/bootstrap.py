from __future__ import annotations

import dataclasses
from functools import partial
from typing import TYPE_CHECKING

from randovania.games.am2r.layout import AM2RConfiguration
from randovania.resolver.bootstrap import Bootstrap
from randovania.resolver.energy_tank_damage_state import EnergyTankDamageState

if TYPE_CHECKING:
    from random import Random

    from randovania.game_description.db.pickup_node import PickupNode
    from randovania.game_description.game_database_view import GameDatabaseView, ResourceDatabaseView
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.generator.pickup_pool import PoolResults
    from randovania.resolver.damage_state import DamageState


def is_dna_node(node: PickupNode, config: AM2RConfiguration) -> bool:
    artifact_config = config.artifacts
    name = node.extra["object_name"]
    _boss_items = ["oItemM_111", "oItemJumpBall", "oItemSpaceJump", "oItemPBeam", "oItemIBeam", "oItemETank_50"]
    return (
        artifact_config.prefer_metroids
        and name.startswith("oItemDNA_")
        or artifact_config.prefer_bosses
        and name in _boss_items
    )


class AM2RBootstrap(Bootstrap[AM2RConfiguration]):
    def create_damage_state(self, game: GameDatabaseView, configuration: AM2RConfiguration) -> DamageState:
        return EnergyTankDamageState(
            configuration.energy_per_tank - 1,
            configuration.energy_per_tank,
            game.get_resource_database_view().get_item("Energy Tank"),
        )

    def _get_enabled_misc_resources(
        self, configuration: AM2RConfiguration, resource_database: ResourceDatabaseView
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

            door_db = configuration.dock_rando.weakness_database
            door_type = door_db.find_type("door")
            open_transition_door = door_db.get_by_weakness("door", "Open Transition")
            are_transitions_shuffled = (
                open_transition_door in configuration.dock_rando.types_state[door_type].can_change_from
            )
            if are_transitions_shuffled:
                enabled_resources.add("ShuffledOpenHatches")

        return enabled_resources

    def _damage_reduction(
        self, configuration: AM2RConfiguration, db: ResourceDatabaseView, current_resources: ResourceCollection
    ) -> float:
        num_suits = sum(
            (1 if current_resources[db.get_item_by_display_name(suit)] else 0)
            for suit in ("Varia Suit", "Gravity Suit")
        )
        dr = 0.0
        if num_suits == 1:
            dr = configuration.first_suit_dr
        elif num_suits >= 2:
            dr = configuration.second_suit_dr

        damage_reduction = 1 - (dr / 100)
        return damage_reduction

    def patch_resource_database(self, db: ResourceDatabase, configuration: AM2RConfiguration) -> ResourceDatabase:
        return dataclasses.replace(db, base_damage_reduction=partial(self._damage_reduction, configuration))

    def assign_pool_results(
        self, rng: Random, configuration: AM2RConfiguration, patches: GamePatches, pool_results: PoolResults
    ) -> GamePatches:
        if configuration.artifacts.prefer_anywhere:
            return super().assign_pool_results(rng, configuration, patches, pool_results)
        pickups_to_preplace = [pickup for pickup in list(pool_results.to_place) if pickup.gui_category.name == "dna"]
        locations = self.all_preplaced_pickup_locations(patches.game, configuration, is_dna_node)
        self.pre_place_pickups(rng, pickups_to_preplace, locations, pool_results, patches.game.game)

        return super().assign_pool_results(rng, configuration, patches, pool_results)
