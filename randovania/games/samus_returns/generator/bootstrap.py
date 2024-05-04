from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.samus_returns.generator.pool_creator import METROID_DNA_CATEGORY
from randovania.games.samus_returns.layout import MSRConfiguration
from randovania.layout.base.dock_rando_configuration import DockRandoMode
from randovania.resolver.bootstrap import MetroidBootstrap

if TYPE_CHECKING:
    from random import Random

    from randovania.game_description.db.pickup_node import PickupNode
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.game_description.resources.resource_info import ResourceGain
    from randovania.generator.pickup_pool import PoolResults
    from randovania.layout.base.base_configuration import BaseConfiguration


def is_dna_node(node: PickupNode, config: BaseConfiguration) -> bool:
    assert isinstance(config, MSRConfiguration)
    artifact_config = config.artifacts
    _boss_indices = [37, 99, 139, 171]
    _stronger_metroid_indices = [177, 178, 181, 185, 186, 187, 188, 192, 193, 199, 200, 202, 205, 209]

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
    elif artifact_config.prefer_bosses and pickup_index in _boss_indices:
        return True

    return False


class MSRBootstrap(MetroidBootstrap):
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

    def assign_pool_results(self, rng: Random, patches: GamePatches, pool_results: PoolResults) -> GamePatches:
        assert isinstance(patches.configuration, MSRConfiguration)
        config = patches.configuration.artifacts

        if config.prefer_anywhere:
            return super().assign_pool_results(rng, patches, pool_results)

        locations = self.all_preplaced_item_locations(patches.game, patches.configuration, is_dna_node)
        self.pre_place_items(rng, locations, pool_results, METROID_DNA_CATEGORY)

        return super().assign_pool_results(rng, patches, pool_results)
