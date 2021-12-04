from random import Random
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_type import ResourceType
from randovania.games.cave_story.layout.cs_configuration import CSConfiguration
from randovania.generator.item_pool import PoolResults
from randovania.generator.item_pool.pool_creator import _extend_pool_results


def pool_creator(results: PoolResults, configuration: CSConfiguration, db: ResourceDatabase, base_patches: GamePatches, rng: Random) -> None:
    if base_patches is None or rng is None:
        return
    
    # puppies
    if not configuration.puppies_anywhere:
        puppy_indices = [p for p in PUPPY_INDICES if p not in results.assignment.keys()]
        rng.shuffle(puppy_indices)
        puppies: list[PickupEntry] = list(filter(lambda p: p.item_category.name == "puppies", results.pickups))
        for p in puppies:
            results.pickups.remove(p)
            results.assignment[puppy_indices.pop()] = p
    
    # weapon to break blocks in first cave (do it this way to ensure a particular distribution chance)
    if base_patches.starting_location.area_name == "Start Point":
        sn_weapons = list(SN_WEAPONS)

        bubble_sn = db.get_by_type_and_index(ResourceType.TRICK, "SNBubbler")
        missile_sn = db.get_by_type_and_index(ResourceType.TRICK, "SNMissiles")
        
        if configuration.trick_level.level_for_trick(bubble_sn).as_number >= 1:
            sn_weapons.add("Bubbler")
        if configuration.trick_level.level_for_trick(missile_sn).as_number >= 1:
            sn_weapons.add("Missile Launcher")
            sn_weapons.add("Super Missile Launcher")
            sn_weapons.add("Progressive Missile Launcher")
        
        weapon_iter = lambda w: (p for p in results.pickups if p.name == w)
        sn_weapons = [next(weapon_iter(w)) for w in sn_weapons if next(weapon_iter(w), None) is not None]
        
        first_cave_indices = [i for i in FIRST_CAVE_INDICES if i not in results.assignment.keys()]
        if first_cave_indices and sn_weapons:
            index = rng.choice(first_cave_indices)
            weapon = rng.choice(sn_weapons)

            results.pickups.remove(weapon)
            results.assignment[index] = weapon


# skip 65 and 67 since they both require all 5 puppies
PUPPY_INDICES = [PickupIndex(i) for i in range(57, 67) if i != 65]

FIRST_CAVE_INDICES = [PickupIndex(32), PickupIndex(33)]

SN_WEAPONS = [
    "Polar Star",
    "Progressive Polar Star",
    "Machine Gun",
    "Blade",
    "Nemesis"
]