from __future__ import annotations

from typing import TYPE_CHECKING, override

from randovania.game_description.db.configurable_node import ConfigurableNode
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.prime_hunters.layout import HuntersConfiguration, force_field_configuration
from randovania.games.prime_hunters.layout.force_field_configuration import LayoutForceFieldRequirement
from randovania.lib.json_lib import JsonType
from randovania.resolver.bootstrap import Bootstrap, ConfigurableNodeBootstrap
from randovania.resolver.energy_tank_damage_state import EnergyTankDamageState

if TYPE_CHECKING:
    from random import Random

    from randovania.game_description.db.pickup_node import PickupNode
    from randovania.game_description.game_database_view import GameDatabaseView
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
    from randovania.generator.pickup_pool import PoolResults
    from randovania.resolver.damage_state import DamageState


def is_boss_location(node: PickupNode, config: HuntersConfiguration) -> bool:
    octolith = node.extra.get("fields", {}).get("model_id")
    if octolith is not None and octolith == 8 and config.octoliths.prefer_bosses:
        return True

    return False


class HuntersBootstrap(Bootstrap[HuntersConfiguration]):
    def create_damage_state(self, game: GameDatabaseView, configuration: HuntersConfiguration) -> DamageState:
        return EnergyTankDamageState(
            configuration.starting_energy,
            100,
            game.get_resource_database_view().get_item("EnergyTank"),
            [],
        )

    def assign_pool_results(
        self, rng: Random, configuration: HuntersConfiguration, patches: GamePatches, pool_results: PoolResults
    ) -> GamePatches:
        pickups_to_preplace = [
            pickup for pickup in list(pool_results.to_place) if pickup.gui_category.name == "octolith"
        ]
        locations = self.all_preplaced_pickup_locations(patches.game, configuration, is_boss_location)
        self.pre_place_pickups(rng, pickups_to_preplace, locations, pool_results, patches.game.game)

        # Shield Keys
        if not configuration.shuffle_shield_keys:
            vanilla_shield_keys = {
                "Alinos EchoHall Shield Key": PickupIndex(95),
                "Alinos ElderPassage Shield Key": PickupIndex(96),
                "Alinos HighGround Shield Key": PickupIndex(97),
                "Alinos CrashSite Shield Key": PickupIndex(94),
                "Alinos CouncilChamber Shield Key": PickupIndex(93),
                "Alinos PistonCave Shield Key": PickupIndex(98),
                "CelestialArchives DataShrine01 Shield Key": PickupIndex(105),
                "CelestialArchives DataShrine03 Shield Key": PickupIndex(106),
                "CelestialArchives SynergyCore Shield Key": PickupIndex(110),
                "CelestialArchives DockingBay Shield Key": PickupIndex(107),
                "CelestialArchives IncubationVault01 Shield Key": PickupIndex(108),
                "CelestialArchives NewArrivalRegistration Shield Key": PickupIndex(109),
                "VDO WeaponsComplexSylux Shield Key": PickupIndex(116),
                "VDO WeaponsComplexPsychoBits Shield Key": PickupIndex(115),
                "VDO CompressionChamber Shield Key": PickupIndex(111),
                "VDO StasisBunkerPuzzle Shield Key": PickupIndex(113),
                "VDO StasisBunkerGuardians Shield Key": PickupIndex(114),
                "VDO FuelStack Shield Key": PickupIndex(112),
                "Arcterra SicTransit Shield Key": PickupIndex(103),
                "Arcterra IceHive Shield Key": PickupIndex(101),
                "Arcterra FrostLabyrinth Shield Key": PickupIndex(100),
                "Arcterra FaultLine Shield Key": PickupIndex(99),
                "Arcterra Sanctorus Shield Key": PickupIndex(102),
                "Arcterra Subterranean Shield Key": PickupIndex(104),
            }

            for pickup_name, location in vanilla_shield_keys.items():
                pickup = next(p for p in pool_results.to_place if p.name == pickup_name)
                pool_results.to_place.remove(pickup)
                pool_results.assignment[location] = pickup

        return super().assign_pool_results(rng, configuration, patches, pool_results)

    @override
    @classmethod
    def _configurable_node_class(cls) -> type[ConfigurableNodeBootstrap]:
        return ForceFieldBootstrap


class ForceFieldBootstrap(ConfigurableNodeBootstrap[HuntersConfiguration, LayoutForceFieldRequirement]):
    @override
    @property
    def category_name(self) -> str:
        return "Force Fields"

    @override
    def get_options(
        self, configuration: HuntersConfiguration, game: GameDescription, node: ConfigurableNode
    ) -> dict[str, LayoutForceFieldRequirement | None]:
        ff_requirement = configuration.force_field_configuration.force_field_requirement
        node_requirement = ff_requirement[node.identifier]

        return self._get_standard_options(
            node_requirement,
            node_requirement.long_name,
            {LayoutForceFieldRequirement.RANDOM},
            {req.long_name: req for req in force_field_configuration.ITEM_NAMES.keys()},
        )

    @override
    def get_requirement(
        self, configuration: HuntersConfiguration, game: GameDescription, node_config: LayoutForceFieldRequirement
    ) -> Requirement:
        resource_db = game.get_resource_database_view()
        force_field = resource_db.get_item(node_config.item_name)
        return ResourceRequirement.simple(force_field)

    @override
    def get_node_config(
        self, configuration: HuntersConfiguration, game: GameDescription, patches: GamePatches, node: ConfigurableNode
    ) -> LayoutForceFieldRequirement:
        force_fields = patches.game_specific["force_fields"]
        return LayoutForceFieldRequirement(force_fields[node.identifier.as_string])

    @override
    def get_default_patches(
        self, configuration: HuntersConfiguration, game: GameDescription, patches: GamePatches
    ) -> GamePatches:
        return patches.assign_game_specific(
            {
                "force_fields": {
                    node.identifier.as_string: LayoutForceFieldRequirement.POWER_BEAM
                    for node in game.region_list.iterate_nodes_of_type(ConfigurableNode)
                }
            }
        )

    @override
    def config_data_to_json(self, value: LayoutForceFieldRequirement) -> JsonType:
        return value.value

    @override
    def json_to_config_data(self, value: JsonType) -> LayoutForceFieldRequirement:
        return LayoutForceFieldRequirement(value)
