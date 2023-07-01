from typing import Sequence

from randovania.game_description.pickup import pickup_category
from randovania.game_description.pickup.ammo_pickup import AmmoPickupDefinition
from randovania.game_description.pickup.standard_pickup import StandardPickupDefinition
from randovania.game_description.resources.location_category import LocationCategory
from randovania.game_description.resources.pickup_entry import PickupEntry, PickupModel, PickupGeneratorParams
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceQuantity
from randovania.games.game import RandovaniaGame
from randovania.games.prime1.patcher import prime_items
from randovania.games.prime2.patcher import echoes_items
from randovania.games.prime3.patcher import corruption_items
from randovania.layout.base.standard_pickup_state import StandardPickupState


def create_standard_pickup(
        pickup: StandardPickupDefinition,
        state: StandardPickupState,
        resource_database: ResourceDatabase,
        ammo: AmmoPickupDefinition | None,
        ammo_requires_main_item: bool,
) -> PickupEntry:
    """
    Creates a Pickup for the given MajorItem
    :param state:
    :param pickup:
    :param resource_database:
    :param ammo:
    :param ammo_requires_main_item:
    :return:
    """

    extra_resources = [
        (resource_database.get_item(ammo_name), ammo_count)
        for ammo_name, ammo_count in zip(pickup.ammo, state.included_ammo)
    ]
    extra_resources.extend(
        (resource_database.get_item(item), count)
        for item, count in pickup.additional_resources.items()
    )

    def _create_resources(base_resource: str | None) -> ResourceQuantity:
        # FIXME: hacky quantity for Hazard Shield
        quantity = 5 if pickup.name == "Hazard Shield" else 1
        return resource_database.get_item(base_resource), quantity

    return PickupEntry(
        name=pickup.name,
        progression=tuple(
            _create_resources(progression)
            for progression in pickup.progression
        ),
        extra_resources=tuple(extra_resources),
        model=PickupModel(
            game=resource_database.game_enum,
            name=pickup.model_name,
        ),
        pickup_category=pickup.pickup_category,
        broad_category=pickup.broad_category,
        unlocks_resource=pickup.unlocks_ammo,
        respects_lock=ammo_requires_main_item,
        resource_lock=ammo.create_resource_lock(resource_database) if ammo is not None else None,
        generator_params=PickupGeneratorParams(
            preferred_location_category=pickup.preferred_location_category,
            probability_offset=pickup.probability_offset,
            probability_multiplier=pickup.probability_multiplier * state.priority,
        ),
    )


def create_ammo_pickup(ammo: AmmoPickupDefinition,
                       ammo_count: Sequence[int],
                       requires_main_item: bool,
                       resource_database: ResourceDatabase,
                       ) -> PickupEntry:
    """
    Creates a Pickup for an expansion of the given ammo.
    :param ammo:
    :param ammo_count:
    :param requires_main_item:
    :param resource_database:
    :return:
    """
    resources = [(resource_database.get_item(item), count)
                 for item, count in zip(ammo.items, ammo_count)]
    resources.extend(
        (resource_database.get_item(item), count)
        for item, count in ammo.additional_resources.items()
    )

    return PickupEntry(
        name=ammo.name,
        progression=(),
        extra_resources=tuple(resources),
        model=PickupModel(
            game=resource_database.game_enum,
            name=ammo.model_name,
        ),
        pickup_category=ammo.pickup_category,
        broad_category=ammo.broad_category,
        respects_lock=requires_main_item,
        resource_lock=ammo.create_resource_lock(resource_database),
        generator_params=PickupGeneratorParams(
            preferred_location_category=ammo.preferred_location_category,
            probability_multiplier=2,
        ),
    )


def create_dark_temple_key(key_number: int,
                           temple_index: int,
                           resource_database: ResourceDatabase,
                           ) -> PickupEntry:
    """
    Creates a Dark Temple Key
    :param key_number:
    :param temple_index: The index of the temple: Dark Agon, Dark Torvus, Hive Temple
    :param resource_database:
    :return:
    """
    TEMPLE_KEY_CATEGORY = pickup_category.PickupCategory(
        name="temple_key",
        long_name="Dark Temple Key",
        hint_details=("a ", "red Temple Key"),
        hinted_as_major=False,
        is_key=True
    )

    return PickupEntry(
        name=echoes_items.DARK_TEMPLE_KEY_NAMES[temple_index].format(key_number + 1),
        progression=((resource_database.get_item(echoes_items.DARK_TEMPLE_KEY_ITEMS[temple_index][key_number]), 1),),
        model=PickupModel(
            game=resource_database.game_enum,
            name=echoes_items.DARK_TEMPLE_KEY_MODEL,
        ),
        pickup_category=TEMPLE_KEY_CATEGORY,
        broad_category=pickup_category.GENERIC_KEY_CATEGORY,
        generator_params=PickupGeneratorParams(
            preferred_location_category=LocationCategory.MAJOR,
            probability_offset=3,
        ),
    )


def create_sky_temple_key(key_number: int,
                          resource_database: ResourceDatabase,
                          ) -> PickupEntry:
    """

    :param key_number:
    :param resource_database:
    :return:
    """
    SKY_TEMPLE_KEY_CATEGORY = pickup_category.PickupCategory(
        name="sky_temple_key",
        long_name="Sky Temple Key",
        hint_details=("a ", "Sky Temple Key"),
        hinted_as_major=False,
        is_key=True
    )

    return PickupEntry(
        name=f"Sky Temple Key {key_number + 1}",
        progression=((resource_database.get_item(echoes_items.SKY_TEMPLE_KEY_ITEMS[key_number]), 1),),
        model=PickupModel(
            game=resource_database.game_enum,
            name=echoes_items.SKY_TEMPLE_KEY_MODEL,
        ),
        pickup_category=SKY_TEMPLE_KEY_CATEGORY,
        broad_category=pickup_category.GENERIC_KEY_CATEGORY,
        generator_params=PickupGeneratorParams(
            preferred_location_category=LocationCategory.MAJOR,
            probability_offset=3,
        ),
    )


def create_dread_artifact(artifact_number: int,
                          resource_database: ResourceDatabase,
                          ) -> PickupEntry:
    DREAD_ARTIFACT_CATEGORY = pickup_category.PickupCategory(
        name="dna",
        long_name="Metroid DNA",
        hint_details=("some ", "Metroid DNA"),
        hinted_as_major=False,
        is_key=True
    )

    return PickupEntry(
        name=f"Metroid DNA {artifact_number + 1}",
        progression=((resource_database.get_item(f"Artifact{artifact_number + 1}"), 1),),
        model=PickupModel(
            game=resource_database.game_enum,
            name=f"DNA_{artifact_number + 1}"
        ),
        pickup_category=DREAD_ARTIFACT_CATEGORY,
        broad_category=pickup_category.GENERIC_KEY_CATEGORY,
        generator_params=PickupGeneratorParams(
            preferred_location_category=LocationCategory.MAJOR,
            probability_offset=0.25,
        ),
    )

def create_am2r_artifact(artifact_number: int,
                          resource_database: ResourceDatabase,
                          ) -> PickupEntry:
    AM2R_ARTIFACT_CATEGORY = pickup_category.PickupCategory(
        name="dna",
        long_name="Metroid DNA",
        hint_details=("some ", "Metroid DNA"),
        hinted_as_major=False,
        is_key=True
    )

    return PickupEntry(
        name=f"Metroid DNA {artifact_number + 1}",
        progression=((resource_database.get_item(f"Metroid DNA {artifact_number + 1}"), 1),),
        model=PickupModel(
            game=resource_database.game_enum,
            name="Metroid DNA"
        ),
        pickup_category=AM2R_ARTIFACT_CATEGORY,
        broad_category=pickup_category.GENERIC_KEY_CATEGORY,
        generator_params=PickupGeneratorParams(
            preferred_location_category=LocationCategory.MAJOR,
            probability_offset=0.25,
        ),
    )


def create_energy_cell(cell_index: int,
                       resource_database: ResourceDatabase,
                       ) -> PickupEntry:
    ENERGY_CELL_CATEGORY = pickup_category.PickupCategory(
        name="energy_cell",
        long_name="Energy Cell",
        hint_details=("an ", "energy cell"),
        hinted_as_major=True,
        is_key=True
    )

    return PickupEntry(
        name=f"Energy Cell {cell_index + 1}",
        progression=(
            (resource_database.get_item(corruption_items.ENERGY_CELL_ITEMS[cell_index]), 1),
        ),
        extra_resources=(
            (resource_database.get_item(corruption_items.ENERGY_CELL_TOTAL_ITEM), 1),
            (resource_database.get_item(corruption_items.PERCENTAGE), 1),
        ),
        model=PickupModel(
            game=resource_database.game_enum,
            name=corruption_items.ENERGY_CELL_MODEL,
        ),
        pickup_category=ENERGY_CELL_CATEGORY,
        broad_category=pickup_category.GENERIC_KEY_CATEGORY,
        generator_params=PickupGeneratorParams(
            preferred_location_category=LocationCategory.MAJOR,
            probability_offset=0.25,
        ),
    )


def create_artifact(artifact_index: int,
                    minimum_progression: int,
                    resource_database: ResourceDatabase,
                    ) -> PickupEntry:
    ARTIFACT_CATEGORY = pickup_category.PickupCategory(
        name="artifact",
        long_name="Artifact",
        hint_details=("an ", "artifact"),
        hinted_as_major=False,
        is_key=True
    )

    return PickupEntry(
        name=prime_items.ARTIFACT_NAMES[artifact_index],
        progression=(
            (resource_database.get_item(prime_items.ARTIFACT_ITEMS[artifact_index]), 1),
        ),
        model=PickupModel(
            game=resource_database.game_enum,
            name=prime_items.ARTIFACT_MODEL[artifact_index],
        ),
        pickup_category=ARTIFACT_CATEGORY,
        broad_category=pickup_category.GENERIC_KEY_CATEGORY,
        generator_params=PickupGeneratorParams(
            preferred_location_category=LocationCategory.MAJOR,
            probability_offset=0.25,
            required_progression=minimum_progression,
        ),
    )


def create_echoes_useless_pickup(resource_database: ResourceDatabase) -> PickupEntry:
    """
    Creates an Energy Transfer Module pickup.
    :param resource_database:
    :return:
    """
    return PickupEntry(
        name="Energy Transfer Module",
        progression=(
            (resource_database.get_item(echoes_items.USELESS_PICKUP_ITEM), 1),
        ),
        model=PickupModel(
            game=resource_database.game_enum,
            name=echoes_items.USELESS_PICKUP_MODEL,
        ),
        pickup_category=pickup_category.USELESS_PICKUP_CATEGORY,
        broad_category=pickup_category.USELESS_PICKUP_CATEGORY,
        generator_params=PickupGeneratorParams(
            preferred_location_category=LocationCategory.MAJOR,  # TODO
        ),
    )


def create_nothing_pickup(resource_database: ResourceDatabase) -> PickupEntry:
    """
    Creates a Nothing pickup.
    :param resource_database:
    :return:
    """
    return PickupEntry(
        name="Nothing",
        progression=(
            (resource_database.get_item_by_name("Nothing"), 1),
        ),
        model=PickupModel(
            game=resource_database.game_enum,
            name="Nothing",
        ),
        pickup_category=pickup_category.USELESS_PICKUP_CATEGORY,
        broad_category=pickup_category.USELESS_PICKUP_CATEGORY,
        generator_params=PickupGeneratorParams(
            preferred_location_category=LocationCategory.MAJOR,  # TODO
        ),
    )


def create_visual_etm() -> PickupEntry:
    """
    Creates an ETM that should only be used as a visual pickup.
    :return:
    """
    return PickupEntry(
        name="Unknown item",
        progression=tuple(),
        model=PickupModel(
            game=RandovaniaGame.METROID_PRIME_ECHOES,
            name=echoes_items.USELESS_PICKUP_MODEL,
        ),
        pickup_category=pickup_category.USELESS_PICKUP_CATEGORY,
        broad_category=pickup_category.USELESS_PICKUP_CATEGORY,
        generator_params=PickupGeneratorParams(
            preferred_location_category=LocationCategory.MAJOR,  # TODO
        ),
    )
