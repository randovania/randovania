from __future__ import annotations

import copy
import dataclasses
from random import Random
from typing import TYPE_CHECKING, override

from randovania.game_description.db.configurable_node import ConfigurableNode
from randovania.game_description.game_database_view import GameDatabaseView, ResourceDatabaseView
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.damage_reduction import DamageReduction
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.games.prime2.layout import translator_configuration
from randovania.games.prime2.layout.echoes_configuration import (
    EchoesConfiguration,
    LayoutSkyTempleKeyMode,
)
from randovania.games.prime2.layout.translator_configuration import LayoutTranslatorRequirement
from randovania.games.prime2_opr.layout.prime2_opr_configuration import EchoesOPRConfiguration
from randovania.generator.pickup_pool import PoolResults
from randovania.lib.json_lib import JsonType
from randovania.resolver.bootstrap import Bootstrap, ConfigurableNodeBootstrap
from randovania.resolver.damage_state import DamageState
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


def is_boss_location(node: PickupNode, config: EchoesConfiguration | EchoesOPRConfiguration) -> bool:
    mode = config.sky_temple_keys
    boss = node.extra.get("boss")
    if boss is not None:
        if boss == "guardian" or mode == LayoutSkyTempleKeyMode.ALL_BOSSES:
            return True

    return False


class BaseEchoesBootstrap[Configuration: (EchoesConfiguration, EchoesOPRConfiguration)](Bootstrap[Configuration]):
    def create_damage_state(self, game: GameDatabaseView, configuration: Configuration) -> DamageState:
        return EnergyTankDamageState(
            configuration.energy_per_tank - 1,
            configuration.energy_per_tank,
            game.get_resource_database_view().get_item("EnergyTank"),
            [],
        )

    def _get_enabled_misc_resources(
        self, configuration: Configuration, resource_database: ResourceDatabaseView
    ) -> set[str]:
        enabled_resources = set()

        if configuration.safe_zone.prevents_dark_aether:
            # Safe Zone
            enabled_resources.add("SafeZone")

        return enabled_resources

    def patch_resource_database(self, db: ResourceDatabase, configuration: Configuration) -> ResourceDatabase:
        damage_reductions = copy.copy(db.damage_reductions)
        damage_reductions[db.get_damage("DarkWorld1")] = [
            DamageReduction(None, 0, configuration.varia_suit_damage / 6.0),
            DamageReduction(db.get_item_by_display_name("Dark Suit"), 1, configuration.dark_suit_damage / 6.0),
            DamageReduction(db.get_item_by_display_name("Light Suit"), 1, 0.0),
        ]
        return dataclasses.replace(db, damage_reductions=damage_reductions)

    def assign_pool_results(
        self, rng: Random, configuration: Configuration, patches: GamePatches, pool_results: PoolResults
    ) -> GamePatches:
        mode = configuration.sky_temple_keys

        if mode == LayoutSkyTempleKeyMode.ALL_BOSSES or mode == LayoutSkyTempleKeyMode.ALL_GUARDIANS:
            pickups_to_preplace = [
                pickup for pickup in list(pool_results.to_place) if pickup.gui_category.name == "sky_temple_key"
            ]
            locations = self.all_preplaced_pickup_locations(patches.game, configuration, is_boss_location)
            self.pre_place_pickups(rng, pickups_to_preplace, locations, pool_results, patches.game.game)

        return super().assign_pool_results(rng, configuration, patches, pool_results)  # type: ignore[arg-type]

    @override
    @classmethod
    def _configurable_node_class(cls) -> type[ConfigurableNodeBootstrap]:
        return TranslatorGateBootstrap


class EchoesBootstrap(BaseEchoesBootstrap[EchoesConfiguration]):
    def event_resources_for_configuration(
        self,
        configuration: EchoesConfiguration,
        resource_database: ResourceDatabaseView,
    ) -> ResourceGain:
        yield resource_database.get_event("Event2"), 1  # Hive Tunnel Web
        yield resource_database.get_event("Event4"), 1  # Command Chamber Gate
        yield resource_database.get_event("Event71"), 1  # Landing Site Webs
        yield resource_database.get_event("Event78"), 1  # Hive Chamber A Gates

        if configuration.use_new_patcher.is_enabled():
            yield resource_database.get_event("Event73"), 1  # Dynamo Chamber Gates
            yield resource_database.get_event("Event75"), 1  # Trooper Security Station Gate

    def _get_enabled_misc_resources(
        self, configuration: EchoesConfiguration, resource_database: ResourceDatabaseView
    ) -> set[str]:
        enabled_resources = super()._get_enabled_misc_resources(configuration, resource_database)
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

        return enabled_resources


class TranslatorGateBootstrap(ConfigurableNodeBootstrap[EchoesConfiguration, LayoutTranslatorRequirement]):
    @override
    @property
    def category_name(self) -> str:
        return "Translator Gates"

    @override
    def get_options(
        self, configuration: EchoesConfiguration, game: GameDescription, node: ConfigurableNode
    ) -> dict[str, LayoutTranslatorRequirement | None]:
        translator_requirement = configuration.translator_configuration.translator_requirement
        gate_requirement = translator_requirement[node.identifier]

        return self._get_standard_options(
            gate_requirement,
            gate_requirement.long_name,
            {
                LayoutTranslatorRequirement.RANDOM,
                LayoutTranslatorRequirement.RANDOM_WITH_REMOVED,
            },
            {translator.long_name: translator for translator in translator_configuration.ITEM_NAMES.keys()},
        )

    @override
    def get_requirement(
        self, configuration: EchoesConfiguration, game: GameDescription, node_config: LayoutTranslatorRequirement
    ) -> Requirement:
        resource_db = game.get_resource_database_view()
        scan_visor = resource_db.get_item_by_display_name("Scan Visor")
        scan_visor_req = ResourceRequirement.simple(scan_visor)

        translator = resource_db.get_item(node_config.item_name)
        translator_req = ResourceRequirement.simple(translator)

        return RequirementAnd([scan_visor_req, translator_req])

    @override
    def get_node_config(
        self, configuration: EchoesConfiguration, game: GameDescription, patches: GamePatches, node: ConfigurableNode
    ) -> LayoutTranslatorRequirement:
        translator_gates = patches.game_specific["translator_gates"]
        return LayoutTranslatorRequirement(translator_gates[node.identifier.as_string])

    @override
    def get_default_patches(
        self, configuration: EchoesConfiguration, game: GameDescription, patches: GamePatches
    ) -> GamePatches:
        return patches.assign_game_specific(
            {
                "translator_gates": {
                    node.identifier.as_string: LayoutTranslatorRequirement.REMOVED
                    for node in game.region_list.iterate_nodes_of_type(ConfigurableNode)
                }
            }
        )

    @override
    def config_data_to_json(self, value: LayoutTranslatorRequirement) -> JsonType:
        return value.value

    @override
    def json_to_config_data(self, value: JsonType) -> LayoutTranslatorRequirement:
        return LayoutTranslatorRequirement(value)
