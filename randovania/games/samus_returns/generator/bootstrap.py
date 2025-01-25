from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.games.samus_returns.layout import MSRConfiguration
from randovania.games.samus_returns.layout.msr_configuration import FinalBossConfiguration
from randovania.layout.base.dock_rando_configuration import DockRandoMode
from randovania.resolver.bootstrap import Bootstrap
from randovania.resolver.energy_tank_damage_state import EnergyTankDamageState

if TYPE_CHECKING:
    from random import Random

    from randovania.game_description.db.pickup_node import PickupNode
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.game_description.resources.resource_info import ResourceGain
    from randovania.generator.pickup_pool import PoolResults
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.resolver.damage_state import DamageState


def is_dna_node(node: PickupNode, config: BaseConfiguration) -> bool:
    assert isinstance(config, MSRConfiguration)
    artifact_config = config.artifacts
    _stronger_metroid_indices = [177, 178, 181, 185, 186, 187, 188, 192, 193, 199, 200, 202, 205, 209]
    _boss_indices = [37, 99, 139, 171, 211]
    _boss_mapping = {
        FinalBossConfiguration.ARACHNUS: 0,
        FinalBossConfiguration.DIGGERNAUT: 2,
        FinalBossConfiguration.QUEEN: 3,
        FinalBossConfiguration.RIDLEY: 4,
    }

    pickup_type = node.extra.get("pickup_type")
    pickup_index = node.pickup_index.index
    # Metroid pickups
    if pickup_type == "metroid":
        if artifact_config.prefer_metroids and artifact_config.prefer_stronger_metroids:
            return True
        elif artifact_config.prefer_metroids and pickup_index not in _stronger_metroid_indices:
            return True
        elif artifact_config.prefer_stronger_metroids and pickup_index in _stronger_metroid_indices:
            return True
    # Boss pickups/locations
    elif artifact_config.prefer_bosses:
        index = _boss_mapping.get(config.final_boss, 4)
        _boss_indices.pop(index)
        if pickup_index in _boss_indices:
            return True

    return False


class MSRBootstrap(Bootstrap):
    def create_damage_state(self, game: GameDescription, configuration: BaseConfiguration) -> DamageState:
        assert isinstance(configuration, MSRConfiguration)
        return EnergyTankDamageState(
            configuration.energy_per_tank - 1,
            configuration.energy_per_tank,
            game.resource_database,
            game.region_list,
        )

    def _get_enabled_misc_resources(
        self, configuration: BaseConfiguration, resource_database: ResourceDatabase
    ) -> set[str]:
        enabled_resources = set()
        assert isinstance(configuration, MSRConfiguration)

        logical_patches = {
            "allow_highly_dangerous_logic": "HighDanger",
            "charge_door_buff": "ChargeDoorBuff",
            "beam_door_buff": "BeamDoorBuff",
            "nerf_super_missiles": "NerfSupers",
            "beam_burst_buff": "BeamBurstBuff",
            "surface_crumbles": "SurfaceCrumbles",
            "area1_crumbles": "Area1Crumbles",
            "reverse_area8": "ReverseArea8",
        }
        for name, index in logical_patches.items():
            if getattr(configuration, name):
                enabled_resources.add(index)

        if configuration.dock_rando.is_enabled():
            enabled_resources.add("DoorLocks")

        if configuration.dock_rando.mode == DockRandoMode.WEAKNESSES:
            enabled_resources.add("DoorLockRandoTypes")

        if configuration.final_boss == FinalBossConfiguration.ARACHNUS:
            enabled_resources.add("FinalBossArachnus")
        elif configuration.final_boss == FinalBossConfiguration.DIGGERNAUT:
            enabled_resources.add("FinalBossDiggernaut")
        # If Queen is the final boss, remove the wall next to the arena
        elif configuration.final_boss == FinalBossConfiguration.QUEEN:
            enabled_resources.add("FinalBossQueen")
            enabled_resources.add("ReverseArea8")
        elif configuration.final_boss == FinalBossConfiguration.RIDLEY:
            enabled_resources.add("FinalBossRidley")

        return enabled_resources

    def event_resources_for_configuration(
        self,
        configuration: BaseConfiguration,
        resource_database: ResourceDatabase,
    ) -> ResourceGain:
        assert isinstance(configuration, MSRConfiguration)

        if configuration.elevator_grapple_blocks:
            for name in [
                "Area 4 (Central Caves) - Transport to Area 3 and Crystal Mines Grapple Block Pull Right",
                "Area 5 (Tower Lobby) - Transport to Areas 4 and 6 Grapple Block Bottom",
                "Area 6 - Transport to Area 7 Grapple Block Pull",
                "Area 7 - Transport to Area 8 Grapple Block",
            ]:
                yield resource_database.get_event(name), 1

        if configuration.area3_interior_shortcut_no_grapple:
            yield (
                resource_database.get_event(
                    "Area 3 (Factory Interior) - Gamma Arena & Transport to Metroid Caverns East Grapple Block"
                ),
                1,
            )

        # If Diggernaut is the final boss, remove the Grapple Blocks by the elevator
        if configuration.final_boss == FinalBossConfiguration.DIGGERNAUT:
            for name in [
                "Area 6 - Transport to Area 7 Grapple Block Pull",
                "Area 6 - Transport to Area 7 Grapple Block Top",
            ]:
                yield resource_database.get_event(name), 1

    def _damage_reduction(self, db: ResourceDatabase, current_resources: ResourceCollection) -> float:
        num_suits = sum(
            (1 if current_resources[db.get_item_by_name(suit)] else 0) for suit in ("Varia Suit", "Gravity Suit")
        )
        dr = 1.0
        if num_suits == 1:
            dr = 0.50
        elif num_suits >= 2:
            dr = 0.25

        return dr

    def patch_resource_database(self, db: ResourceDatabase, configuration: BaseConfiguration) -> ResourceDatabase:
        return dataclasses.replace(db, base_damage_reduction=self._damage_reduction)

    def assign_pool_results(self, rng: Random, patches: GamePatches, pool_results: PoolResults) -> GamePatches:
        assert isinstance(patches.configuration, MSRConfiguration)
        config = patches.configuration.artifacts

        if config.prefer_anywhere:
            return super().assign_pool_results(rng, patches, pool_results)

        locations = self.all_preplaced_item_locations(patches.game, patches.configuration, is_dna_node)
        self.pre_place_items(rng, locations, pool_results, "dna", patches.game.game)

        return super().assign_pool_results(rng, patches, pool_results)
