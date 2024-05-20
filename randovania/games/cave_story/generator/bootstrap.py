from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description import default_database
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.cave_story.layout.cs_configuration import CSConfiguration, CSObjective
from randovania.resolver.bootstrap import Bootstrap, EnergyConfig

if TYPE_CHECKING:
    from collections.abc import Iterator
    from random import Random

    from randovania.game_description.db.pickup_node import PickupNode
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.game_description.resources.resource_info import ResourceGain
    from randovania.generator.pickup_pool import PoolResults
    from randovania.layout.base.base_configuration import BaseConfiguration


def is_puppy_node(node: PickupNode, config: BaseConfiguration) -> bool:
    # skip 65 and 67 since they both require all 5 puppies
    PUPPY_INDICES = [PickupIndex(i) for i in range(57, 67) if i != 65]
    return node.pickup_index in PUPPY_INDICES


class CSBootstrap(Bootstrap):
    def _get_enabled_misc_resources(
        self, configuration: BaseConfiguration, resource_database: ResourceDatabase
    ) -> set[str]:
        assert isinstance(configuration, CSConfiguration)
        enabled_resources = set()

        objectives = {
            CSObjective.BAD_ENDING: "badEnd",
            CSObjective.NORMAL_ENDING: "normalEnd",
            CSObjective.BEST_ENDING: "bestEnd",
            CSObjective.ALL_BOSSES: "allBosses",
            CSObjective.HUNDRED_PERCENT: "hundo",
        }
        enabled_resources.add(objectives[configuration.objective])

        enabled_resources.add("PONR")

        return enabled_resources

    def version_resources_for_game(
        self, configuration: BaseConfiguration, resource_database: ResourceDatabase
    ) -> ResourceGain:
        assert isinstance(configuration, CSConfiguration)
        for resource in resource_database.version:
            yield resource, 1 if resource.long_name == "Freeware" else 0

    def energy_config(self, configuration: BaseConfiguration) -> EnergyConfig:
        assert isinstance(configuration, CSConfiguration)
        return EnergyConfig(configuration.starting_hp, 1)

    def assign_pool_results(self, rng: Random, patches: GamePatches, results: PoolResults) -> GamePatches:
        configuration = patches.configuration
        assert isinstance(configuration, CSConfiguration)

        db = patches.game.resource_database

        def get_valid_indices(indices: list[PickupIndex]) -> list[PickupIndex]:
            return [p for p in indices if p not in results.assignment.keys()]

        def get_valid_pickups(pickups: list[str]) -> list[PickupEntry]:
            def pickup_iter(w: str) -> Iterator[PickupEntry]:
                return (p for p in results.to_place if p.name == w)

            return [next(pickup_iter(w)) for w in pickups if next(pickup_iter(w), None) is not None]

        # puppies
        if not configuration.puppies_anywhere:
            pickup_database = default_database.pickup_database_for_game(patches.game.game)
            puppies_category = pickup_database.pickup_categories["puppies"]
            locations = self.all_preplaced_item_locations(patches.game, patches.configuration, is_puppy_node)
            self.pre_place_items(rng, locations, results, puppies_category)

        # weapon to break blocks in first cave (do it this way to ensure a particular distribution chance)
        if patches.starting_location.area in {"Start Point", "First Cave", "Hermit Gunsmith"}:
            _sn_weapons = list(SN_WEAPONS)

            bubble_sn = db.get_trick("SNBubbler")
            missile_sn = db.get_trick("SNMissiles")

            if configuration.trick_level.level_for_trick(bubble_sn).is_enabled:
                _sn_weapons.append("Bubbler")
            if configuration.trick_level.level_for_trick(missile_sn).is_enabled:
                _sn_weapons.extend({"Missile Launcher", "Super Missile Launcher", "Progressive Missile Launcher"})

            sn_weapons = get_valid_pickups(_sn_weapons)

            first_cave_indices = get_valid_indices(FIRST_CAVE_INDICES)
            if first_cave_indices and sn_weapons:
                index = rng.choice(first_cave_indices)
                weapon = rng.choice(sn_weapons)

                results.to_place.remove(weapon)
                results.assignment[index] = weapon

        # strong weapon and life capsule in camp
        if patches.starting_location.area == "Camp":
            strong_weapons = get_valid_pickups(STRONG_WEAPONS)
            life_capsules = get_valid_pickups(["5HP Life Capsule"])
            camp_indices = get_valid_indices(CAMP_INDICES)

            rng.shuffle(camp_indices)

            if camp_indices and strong_weapons:
                weapon = rng.choice(strong_weapons)
                results.assignment[camp_indices.pop()] = weapon
                results.to_place.remove(weapon)
            if camp_indices and life_capsules:
                life_capsule = rng.choice(life_capsules)
                results.assignment[camp_indices.pop()] = life_capsule
                results.to_place.remove(life_capsule)

        return super().assign_pool_results(rng, patches, results)


FIRST_CAVE_INDICES = [PickupIndex(32), PickupIndex(33)]

CAMP_INDICES = [PickupIndex(26), PickupIndex(27)]

SN_WEAPONS = [
    "Polar Star",
    "Progressive Polar Star",
    "Spur",
    "Machine Gun",
    "Blade",
    "Nemesis",
]

STRONG_WEAPONS = [
    "Blade",
    "Nemesis",
    "Machine Gun",
    "Spur",
    "Snake",
]
