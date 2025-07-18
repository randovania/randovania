from __future__ import annotations

import copy
import dataclasses
from typing import TYPE_CHECKING

from randovania.game_description.db.configurable_node import ConfigurableNode
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources import search
from randovania.game_description.resources.damage_reduction import DamageReduction
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration, LayoutSkyTempleKeyMode
from randovania.games.prime2.layout.translator_configuration import LayoutTranslatorRequirement
from randovania.resolver.bootstrap import Bootstrap
from randovania.resolver.energy_tank_damage_state import EnergyTankDamageState

if TYPE_CHECKING:
    from random import Random

    from randovania.game_description.db.pickup_node import PickupNode
    from randovania.game_description.game_database_view import GameDatabaseView, ResourceDatabaseView
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.game_description.resources.resource_info import ResourceGain
    from randovania.generator.pickup_pool import PoolResults
    from randovania.resolver.damage_state import DamageState


def is_boss_location(node: PickupNode, config: EchoesConfiguration) -> bool:
    mode = config.sky_temple_keys
    boss = node.extra.get("boss")
    if boss is not None:
        if boss == "guardian" or mode == LayoutSkyTempleKeyMode.ALL_BOSSES:
            return True

    return False


class EchoesBootstrap(Bootstrap[EchoesConfiguration]):
    def create_damage_state(self, game: GameDatabaseView, configuration: EchoesConfiguration) -> DamageState:
        return EnergyTankDamageState(
            configuration.energy_per_tank - 1,
            configuration.energy_per_tank,
            game.get_resource_database_view().get_item("EnergyTank"),
        )

    def event_resources_for_configuration(
        self,
        configuration: EchoesConfiguration,
        resource_database: ResourceDatabaseView,
    ) -> ResourceGain:
        yield resource_database.get_event("Event2"), 1  # Hive Tunnel Web
        yield resource_database.get_event("Event4"), 1  # Command Chamber Gate
        yield resource_database.get_event("Event71"), 1  # Landing Site Webs
        yield resource_database.get_event("Event78"), 1  # Hive Chamber A Gates

        if configuration.use_new_patcher:
            yield resource_database.get_event("Event73"), 1  # Dynamo Chamber Gates
            yield resource_database.get_event("Event75"), 1  # Trooper Security Station Gate
            yield resource_database.get_event("Event20"), 1  # Security Station B DS Appearance

    def _get_enabled_misc_resources(
        self, configuration: EchoesConfiguration, resource_database: ResourceDatabaseView
    ) -> set[str]:
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

    def patch_resource_database(self, db: ResourceDatabase, configuration: EchoesConfiguration) -> ResourceDatabase:
        damage_reductions = copy.copy(db.damage_reductions)
        damage_reductions[db.get_damage("DarkWorld1")] = [
            DamageReduction(None, configuration.varia_suit_damage / 6.0),
            DamageReduction(db.get_item_by_display_name("Dark Suit"), configuration.dark_suit_damage / 6.0),
            DamageReduction(db.get_item_by_display_name("Light Suit"), 0.0),
        ]
        return dataclasses.replace(db, damage_reductions=damage_reductions)

    def assign_pool_results(
        self, rng: Random, configuration: EchoesConfiguration, patches: GamePatches, pool_results: PoolResults
    ) -> GamePatches:
        mode = configuration.sky_temple_keys

        if mode == LayoutSkyTempleKeyMode.ALL_BOSSES or mode == LayoutSkyTempleKeyMode.ALL_GUARDIANS:
            pickups_to_preplace = [
                pickup for pickup in list(pool_results.to_place) if pickup.gui_category.name == "sky_temple_key"
            ]
            locations = self.all_preplaced_pickup_locations(patches.game, configuration, is_boss_location)
            self.pre_place_pickups(rng, pickups_to_preplace, locations, pool_results, patches.game.game)

        return super().assign_pool_results(rng, configuration, patches, pool_results)

    def apply_game_specific_patches(
        self, configuration: EchoesConfiguration, game: GameDescription, patches: GamePatches
    ) -> None:
        scan_visor = search.find_resource_info_with_long_name(game.resource_database.item, "Scan Visor")
        scan_visor_req = ResourceRequirement.simple(scan_visor)

        translator_gates = patches.game_specific["translator_gates"]

        for _, _, node in game.iterate_nodes_of_type(ConfigurableNode):
            requirement = LayoutTranslatorRequirement(translator_gates[node.identifier.as_string])
            translator = game.resource_database.get_item(requirement.item_name)
            game.region_list.configurable_nodes[node.identifier] = RequirementAnd(
                [
                    scan_visor_req,
                    ResourceRequirement.simple(translator),
                ]
            )
