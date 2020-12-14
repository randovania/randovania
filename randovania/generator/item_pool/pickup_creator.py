from typing import Optional, Tuple, List

from randovania.game_description.item.ammo import Ammo
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.item.major_item import MajorItem
from randovania.game_description.resources.pickup_entry import ConditionalResources, ResourceConversion, PickupEntry
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceQuantity
from randovania.games.prime import corruption_items
from randovania.games.prime import prime_items
from randovania.games.prime.echoes_items import DARK_TEMPLE_KEY_MODEL, DARK_TEMPLE_KEY_NAMES, DARK_TEMPLE_KEY_ITEMS, \
    SKY_TEMPLE_KEY_MODEL, SKY_TEMPLE_KEY_ITEMS, USELESS_PICKUP_MODEL, USELESS_PICKUP_ITEM
from randovania.layout.major_item_state import MajorItemState
from randovania.resolver.exceptions import InvalidConfiguration


def create_major_item(item: MajorItem,
                      state: MajorItemState,
                      include_percentage: bool,
                      resource_database: ResourceDatabase,
                      ammo: Optional[Ammo],
                      ammo_requires_major_item: bool,

                      ) -> PickupEntry:
    """
    Creates a Pickup for the given MajorItem
    :param include_percentage:
    :param state:
    :param item:
    :param resource_database:
    :param ammo:
    :param ammo_requires_major_item:
    :return:
    """

    def _create_resources(base_resource: Optional[int],
                          temporary_ammo: bool = False) -> Tuple[ResourceQuantity, ...]:
        resources = []

        if base_resource is not None:
            # FIXME: hacky quantity for Hazard Shield
            quantity = 5 if item.name == "Hazard Shield" else 1
            resources.append((resource_database.get_item(base_resource), quantity))

        for ammo_index, ammo_count in zip(ammo.temporaries if temporary_ammo else item.ammo_index,
                                          state.included_ammo):
            resources.append((resource_database.get_item(ammo_index), ammo_count))

        if include_percentage:
            resources.append((resource_database.item_percentage, 1))

        return tuple(resources)

    if item.progression:
        if ammo_requires_major_item and ammo.unlocked_by != item.progression[0] and ammo.unlocked_by is not None:
            if len(item.progression) != 1:
                raise InvalidConfiguration(
                    ("Item {item.name} uses ammo {ammo.name} that is locked behind {ammo.unlocked_by},"
                     "but it also has progression. This is unsupported.").format(
                        ammo=ammo,
                        item=item,
                    )
                )

            name = resource_database.get_item(item.progression[0]).long_name
            conditional_resources = (
                ConditionalResources(
                    name=name,
                    item=None,
                    resources=_create_resources(item.progression[0], True)
                ),
                ConditionalResources(
                    name=name,
                    item=resource_database.get_item(ammo.unlocked_by),
                    resources=_create_resources(item.progression[0])
                )
            )
        else:
            conditional_resources = tuple(
                ConditionalResources(
                    name=resource_database.get_item(item.progression[i]).long_name,
                    item=resource_database.get_item(item.progression[i - 1]) if i > 0 else None,
                    resources=_create_resources(progression)
                )
                for i, progression in enumerate(item.progression)
            )
    else:
        conditional_resources = (
            ConditionalResources(name=item.name, item=None, resources=_create_resources(None)),
        )

    if item.converts_indices:
        assert len(item.converts_indices) == len(item.ammo_index)
        convert_resources = tuple(
            ResourceConversion(
                source=resource_database.get_item(source),
                target=resource_database.get_item(target),
            )
            for source, target in zip(item.converts_indices, item.ammo_index)
        )
    else:
        convert_resources = tuple()

    return PickupEntry(
        name=item.name,
        resources=conditional_resources,
        model_index=item.model_index,
        item_category=item.item_category,
        broad_category=item.broad_category,
        probability_offset=item.probability_offset,
        probability_multiplier=item.probability_multiplier,
        convert_resources=convert_resources,
    )


def create_ammo_expansion(ammo: Ammo,
                          ammo_count: List[int],
                          requires_major_item: bool,
                          resource_database: ResourceDatabase,
                          ) -> PickupEntry:
    """
    Creates a Pickup for an expansion of the given ammo.
    :param ammo:
    :param ammo_count:
    :param requires_major_item:
    :param resource_database:
    :return:
    """
    resources = [(resource_database.get_item(item), count)
                 for item, count in zip(ammo.items, ammo_count)]
    resources.append((resource_database.item_percentage, 1))

    if ammo.unlocked_by is not None and requires_major_item:
        temporary_resources = [(resource_database.get_item(item), count)
                               for item, count in zip(ammo.temporaries, ammo_count)]
        temporary_resources.append((resource_database.item_percentage, 1))

        conditional_resources = (
            ConditionalResources(temporary_resources[0][0].long_name, None, tuple(temporary_resources)),
            ConditionalResources(ammo.name, resource_database.get_item(ammo.unlocked_by), tuple(resources)),
        )
    else:
        conditional_resources = (
            ConditionalResources(None, None, tuple(resources)),
        )

    return PickupEntry(
        name=ammo.name,
        resources=conditional_resources,
        model_index=ammo.models[0],  # TODO: use a random model
        item_category=ItemCategory.EXPANSION,
        broad_category=ammo.broad_category,
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

    return PickupEntry(
        name=DARK_TEMPLE_KEY_NAMES[temple_index].format(key_number + 1),
        resources=(
            ConditionalResources(None, None, tuple([
                (resource_database.get_item(DARK_TEMPLE_KEY_ITEMS[temple_index][key_number]), 1)
            ])),
        ),
        model_index=DARK_TEMPLE_KEY_MODEL,
        item_category=ItemCategory.TEMPLE_KEY,
        broad_category=ItemCategory.KEY,
        probability_offset=3,
    )


def create_sky_temple_key(key_number: int,
                          resource_database: ResourceDatabase,
                          ) -> PickupEntry:
    """

    :param key_number:
    :param resource_database:
    :return:
    """

    return PickupEntry(
        name="Sky Temple Key {}".format(key_number + 1),
        resources=(
            ConditionalResources(None, None, tuple([
                (resource_database.get_item(SKY_TEMPLE_KEY_ITEMS[key_number]), 1)
            ])),
        ),
        model_index=SKY_TEMPLE_KEY_MODEL,
        item_category=ItemCategory.SKY_TEMPLE_KEY,
        broad_category=ItemCategory.KEY,
        probability_offset=3,
    )


def create_energy_cell(cell_index: int,
                       resource_database: ResourceDatabase,
                       ) -> PickupEntry:
    return PickupEntry(
        name=f"Energy Cell {cell_index + 1}",
        resources=(
            ConditionalResources(None, None, tuple([
                (resource_database.get_item(corruption_items.ENERGY_CELL_ITEMS[cell_index]), 1),
                (resource_database.get_item(corruption_items.ENERGY_CELL_TOTAL_ITEM), 1),
                (resource_database.item_percentage, 1),
            ])),
        ),
        model_index=corruption_items.ENERGY_CELL_MODEL,
        item_category=ItemCategory.TEMPLE_KEY,
        broad_category=ItemCategory.KEY,
        probability_offset=0.25,
    )


def create_artifact(artifact_index: int,
                    resource_database: ResourceDatabase,
                    ) -> PickupEntry:
    return PickupEntry(
        name=prime_items.ARTIFACT_NAMES[artifact_index],
        resources=(
            ConditionalResources(None, None, tuple([
                (resource_database.get_item(prime_items.ARTIFACT_ITEMS[artifact_index]), 1),
                (resource_database.item_percentage, 1)
            ])),
        ),
        model_index=prime_items.ARTIFACT_MODEL[artifact_index],
        item_category=ItemCategory.TEMPLE_KEY,
        broad_category=ItemCategory.KEY,
        probability_offset=0.25,
    )


def create_useless_pickup(resource_database: ResourceDatabase) -> PickupEntry:
    """
    Creates an Energy Transfer Module pickup.
    :param resource_database:
    :return:
    """
    return PickupEntry(
        name="Energy Transfer Module",
        resources=(
            ConditionalResources(None, None, tuple([
                (resource_database.get_item(USELESS_PICKUP_ITEM), 1)
            ])),
        ),
        model_index=USELESS_PICKUP_MODEL,
        item_category=ItemCategory.ETM,
        broad_category=ItemCategory.ETM,
    )


def create_visual_etm() -> PickupEntry:
    """
    Creates an ETM that should only be used as a visual pickup.
    :return:
    """
    return PickupEntry(
        name="Unknown item",
        resources=(
            ConditionalResources(None, None, tuple()),
        ),
        model_index=USELESS_PICKUP_MODEL,
        item_category=ItemCategory.ETM,
        broad_category=ItemCategory.ETM,
    )
