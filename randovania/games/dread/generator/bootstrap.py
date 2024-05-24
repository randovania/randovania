from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.dread.generator.pool_creator import DREAD_ARTIFACT_CATEGORY
from randovania.games.dread.layout.dread_configuration import DreadConfiguration
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
    assert isinstance(config, DreadConfiguration)
    artifact_config = config.artifacts
    return (
        # must be a boss
        "boss_hint_name" in node.extra
        and (
            # must be an emmi with emmi option
            node.extra["pickup_type"] == "emmi"
            and artifact_config.prefer_emmi
            or
            # or not an emmi but with major boss option
            not node.extra["pickup_type"] == "emmi"
            and artifact_config.prefer_major_bosses
        )
    )


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
        locations = self.all_preplaced_item_locations(patches.game, patches.configuration, is_dna_node)
        self.pre_place_items(rng, locations, pool_results, DREAD_ARTIFACT_CATEGORY)
        return super().assign_pool_results(rng, patches, pool_results)
