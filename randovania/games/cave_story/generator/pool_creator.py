from random import Random

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_type import ResourceType
from randovania.games.cave_story.layout.cs_configuration import CSConfiguration
from randovania.generator.base_patches_factory import MissingRng
from randovania.generator.item_pool import PoolResults
from randovania.layout.base.base_configuration import BaseConfiguration


def pool_creator(results: PoolResults,
                 configuration: BaseConfiguration,
                 db: ResourceDatabase,
                 base_patches: GamePatches,
                 rng: Random) -> None:
    assert isinstance(configuration, CSConfiguration)
    if rng is None:
        raise MissingRng("Pool Creator")
    if base_patches is None:
        return

    def get_valid_indices(indices):
        return [p for p in indices if p not in results.assignment.keys()]

    def get_valid_pickups(pickups):
        pickup_iter = lambda w: (p for p in results.pickups if p.name == w)
        return [next(pickup_iter(w)) for w in pickups if next(pickup_iter(w), None) is not None]

    # puppies
    if not configuration.puppies_anywhere:
        puppy_indices = get_valid_indices(PUPPY_INDICES)
        rng.shuffle(puppy_indices)
        puppies: list[PickupEntry] = list(filter(lambda p: p.item_category.name == "puppies", results.pickups))
        for p in puppies:
            results.pickups.remove(p)
            results.assignment[puppy_indices.pop()] = p

    # weapon to break blocks in first cave (do it this way to ensure a particular distribution chance)
    if base_patches.starting_location.area_name in {"Start Point", "First Cave", "Hermit Gunsmith"}:
        sn_weapons = list(SN_WEAPONS)

        bubble_sn = db.get_by_type_and_index(ResourceType.TRICK, "SNBubbler")
        missile_sn = db.get_by_type_and_index(ResourceType.TRICK, "SNMissiles")

        if configuration.trick_level.level_for_trick(bubble_sn).is_enabled:
            sn_weapons.append("Bubbler")
        if configuration.trick_level.level_for_trick(missile_sn).is_enabled:
            sn_weapons.extend({"Missile Launcher", "Super Missile Launcher", "Progressive Missile Launcher"})

        sn_weapons = get_valid_pickups(sn_weapons)

        first_cave_indices = get_valid_indices(FIRST_CAVE_INDICES)
        if first_cave_indices and sn_weapons:
            index = rng.choice(first_cave_indices)
            weapon = rng.choice(sn_weapons)

            results.pickups.remove(weapon)
            results.assignment[index] = weapon

    # strong weapon and life capsule in camp
    if base_patches.starting_location.area_name == "Camp":
        strong_weapons = get_valid_pickups(STRONG_WEAPONS)
        life_capsules = get_valid_pickups(["5HP Life Capsule"])
        camp_indices = get_valid_indices(CAMP_INDICES)

        rng.shuffle(camp_indices)

        if camp_indices and strong_weapons:
            results.assignment[camp_indices.pop()] = rng.choice(strong_weapons)
        if camp_indices and life_capsules:
            results.assignment[camp_indices.pop()] = rng.choice(life_capsules)


# skip 65 and 67 since they both require all 5 puppies
PUPPY_INDICES = [PickupIndex(i) for i in range(57, 67) if i != 65]

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
