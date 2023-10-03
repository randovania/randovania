from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.db.pickup_node import PickupNode
from randovania.games.dread.generator.pool_creator import DREAD_ARTIFACT_CATEGORY
from randovania.games.dread.layout.dread_configuration import DreadArtifactConfig, DreadConfiguration
from randovania.layout.exceptions import InvalidConfiguration
from randovania.resolver.bootstrap import MetroidBootstrap

if TYPE_CHECKING:
    from random import Random

    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.game_description.resources.resource_info import ResourceGain
    from randovania.generator.pickup_pool import PoolResults
    from randovania.layout.base.base_configuration import BaseConfiguration


def all_dna_locations(game: GameDescription, config: DreadArtifactConfig):
    locations = []

    for node in game.region_list.all_nodes:
        if isinstance(node, PickupNode) and "boss_hint_name" in node.extra:
            if node.extra["pickup_type"] == "emmi":
                if config.prefer_emmi:
                    locations.append(node)
            else:
                if config.prefer_major_bosses:
                    locations.append(node)

    return locations


class DreadBootstrap(MetroidBootstrap):
    def _get_enabled_misc_resources(
        self, configuration: BaseConfiguration, resource_database: ResourceDatabase
    ) -> set[str]:
        assert isinstance(configuration, DreadConfiguration)

        enabled_resources = {"SeparateBeams", "SeparateMissiles"}

        logical_patches = {
            "allow_highly_dangerous_logic": "HighDanger",
            "nerf_power_bombs": "NerfPowerBombs",
        }
        for name, index in logical_patches.items():
            if getattr(configuration, name):
                enabled_resources.add(index)

        if configuration.dock_rando.is_enabled():
            enabled_resources.add("DoorLocks")

        if not configuration.teleporters.is_vanilla:
            enabled_resources.add("Teleporters")

        return enabled_resources

    def event_resources_for_configuration(
        self,
        configuration: BaseConfiguration,
        resource_database: ResourceDatabase,
    ) -> ResourceGain:
        assert isinstance(configuration, DreadConfiguration)

        if configuration.hanubia_shortcut_no_grapple:
            for name in ["s080_shipyard:default:grapplepulloff1x2_000", "s080_shipyard:default:grapplepulloff1x2"]:
                yield resource_database.get_event(name), 1

        if configuration.hanubia_easier_path_to_itorash:
            yield resource_database.get_event("s080_shipyard:default:grapplepulloff1x2_001"), 1

        if configuration.x_starts_released:
            yield resource_database.get_event("ElunReleaseX"), 1

    def assign_pool_results(self, rng: Random, patches: GamePatches, pool_results: PoolResults) -> GamePatches:
        assert isinstance(patches.configuration, DreadConfiguration)
        config = patches.configuration.artifacts

        locations = all_dna_locations(patches.game, config)
        rng.shuffle(locations)

        all_dna = [
            pickup for pickup in list(pool_results.to_place) if pickup.pickup_category is DREAD_ARTIFACT_CATEGORY
        ]
        if len(all_dna) > len(locations):
            raise InvalidConfiguration(
                f"Has {len(all_dna)} DNA in the pool, but only {len(locations)} valid locations."
            )

        for dna, location in zip(all_dna, locations, strict=False):
            pool_results.to_place.remove(dna)
            pool_results.assignment[location.pickup_index] = dna

        return super().assign_pool_results(rng, patches, pool_results)
