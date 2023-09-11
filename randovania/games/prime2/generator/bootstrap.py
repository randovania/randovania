from __future__ import annotations

import copy
import dataclasses
from typing import TYPE_CHECKING

from randovania.game_description.resources.damage_reduction import DamageReduction
from randovania.game_description.resources.resource_type import ResourceType
from randovania.games.prime2.generator.pickup_pool import sky_temple_keys
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration, LayoutSkyTempleKeyMode
from randovania.layout.exceptions import InvalidConfiguration
from randovania.resolver.bootstrap import MetroidBootstrap

if TYPE_CHECKING:
    from random import Random

    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.game_description.resources.resource_info import ResourceGain
    from randovania.generator.pickup_pool import PoolResults
    from randovania.layout.base.base_configuration import BaseConfiguration


class EchoesBootstrap(MetroidBootstrap):
    def event_resources_for_configuration(
        self,
        configuration: BaseConfiguration,
        resource_database: ResourceDatabase,
    ) -> ResourceGain:
        assert isinstance(configuration, EchoesConfiguration)
        if configuration.use_new_patcher:
            yield resource_database.get_event("Event73"), 1  # Dynamo Chamber Gates
            yield resource_database.get_event("Event75"), 1  # Trooper Security Station Gate
            yield resource_database.get_event("Event20"), 1  # Security Station B DS Appearance

    def _get_enabled_misc_resources(
        self, configuration: BaseConfiguration, resource_database: ResourceDatabase
    ) -> set[str]:
        assert isinstance(configuration, EchoesConfiguration)
        enabled_resources = set()
        allow_vanilla = {
            "allow_jumping_on_dark_water": "DarkWaterJump",
            "allow_vanilla_dark_beam": "VanillaDarkBeam",
            "allow_vanilla_light_beam": "VanillaLightBeam",
            "allow_vanilla_seeker_launcher": "VanillaSeekers",
            "allow_vanilla_echo_visor": "VanillaEcho",
            "allow_vanilla_dark_visor": "VanillaDarkVisor",
            "allow_vanilla_screw_attack": "VanillaSA",
            "allow_vanilla_gravity_boost": "VanillaGravity",
            "allow_vanilla_boost_ball": "VanillaBoost",
            "allow_vanilla_spider_ball": "VanillaSpider",
        }
        for name, index in allow_vanilla.items():
            if getattr(configuration, name):
                enabled_resources.add(index)

        if configuration.teleporters.is_vanilla:
            # Vanilla Great Temple Emerald Translator Gate
            enabled_resources.add("VanillaGreatTempleEmeraldGate")

        if configuration.safe_zone.prevents_dark_aether:
            # Safe Zone
            enabled_resources.add("SafeZone")

        return enabled_resources

    def patch_resource_database(self, db: ResourceDatabase, configuration: BaseConfiguration) -> ResourceDatabase:
        assert isinstance(configuration, EchoesConfiguration)

        damage_reductions = copy.copy(db.damage_reductions)
        damage_reductions[db.get_by_type_and_index(ResourceType.DAMAGE, "DarkWorld1")] = [
            DamageReduction(None, configuration.varia_suit_damage / 6.0),
            DamageReduction(db.get_item_by_name("Dark Suit"), configuration.dark_suit_damage / 6.0),
            DamageReduction(db.get_item_by_name("Light Suit"), 0.0),
        ]
        return dataclasses.replace(db, damage_reductions=damage_reductions)

    def assign_pool_results(self, rng: Random, patches: GamePatches, pool_results: PoolResults) -> GamePatches:
        assert isinstance(patches.configuration, EchoesConfiguration)
        mode = patches.configuration.sky_temple_keys

        if mode == LayoutSkyTempleKeyMode.ALL_BOSSES or mode == LayoutSkyTempleKeyMode.ALL_GUARDIANS:
            locations = sky_temple_keys.pickup_nodes_for_stk_mode(patches.game, mode)
            rng.shuffle(locations)

            keys = [
                pickup
                for pickup in list(pool_results.to_place)
                if pickup.pickup_category is sky_temple_keys.SKY_TEMPLE_KEY_CATEGORY
            ]

            if len(keys) < len(locations):
                raise InvalidConfiguration(
                    f"Has {len(locations)} boss locations to fill, but only {len(keys)} Sky Temple Keys in the pool."
                )

            for key, location in zip(keys, locations, strict=False):
                pool_results.to_place.remove(key)
                pool_results.assignment[location.pickup_index] = key

        return super().assign_pool_results(rng, patches, pool_results)
