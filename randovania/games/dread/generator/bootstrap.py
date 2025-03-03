from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.dread.layout.dread_configuration import DreadConfiguration
from randovania.resolver.bootstrap import Bootstrap
from randovania.resolver.energy_tank_damage_state import EnergyTankDamageState

if TYPE_CHECKING:
    from random import Random

    from randovania.game_description.db.pickup_node import PickupNode
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.game_description.resources.resource_info import ResourceGain
    from randovania.generator.pickup_pool import PoolResults
    from randovania.resolver.damage_state import DamageState


def is_dna_node(node: PickupNode, config: DreadConfiguration) -> bool:
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


class DreadBootstrap(Bootstrap[DreadConfiguration]):
    def create_damage_state(self, game: GameDescription, configuration: DreadConfiguration) -> DamageState:
        return EnergyTankDamageState(
            configuration.energy_per_tank - 1,
            configuration.energy_per_tank,
            game.resource_database,
            game.region_list,
        )

    def _get_enabled_misc_resources(
        self, configuration: DreadConfiguration, resource_database: ResourceDatabase
    ) -> set[str]:
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
        configuration: DreadConfiguration,
        resource_database: ResourceDatabase,
    ) -> ResourceGain:
        if configuration.hanubia_shortcut_no_grapple:
            for name in ["s080_shipyard:default:grapplepulloff1x2_000", "s080_shipyard:default:grapplepulloff1x2"]:
                yield resource_database.get_event(name), 1

        if configuration.hanubia_easier_path_to_itorash:
            yield resource_database.get_event("s080_shipyard:default:grapplepulloff1x2_001"), 1

        if configuration.x_starts_released:
            yield resource_database.get_event("ElunReleaseX"), 1

    def assign_pool_results(
        self, rng: Random, configuration: DreadConfiguration, patches: GamePatches, pool_results: PoolResults
    ) -> GamePatches:
        locations = self.all_preplaced_pickup_locations(patches.game, configuration, is_dna_node)
        self.pre_place_pickups(rng, locations, pool_results, "dna", patches.game.game)
        return super().assign_pool_results(rng, configuration, patches, pool_results)
