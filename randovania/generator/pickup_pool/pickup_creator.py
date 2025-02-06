from __future__ import annotations

from typing import TYPE_CHECKING

from frozendict import frozendict

from randovania.game_description import default_database, hint_features
from randovania.game_description.pickup.pickup_entry import PickupEntry, PickupGeneratorParams, PickupModel
from randovania.game_description.resources.location_category import LocationCategory

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any

    from randovania.game.game_enum import RandovaniaGame
    from randovania.game_description.pickup.pickup_definition.ammo_pickup import AmmoPickupDefinition
    from randovania.game_description.pickup.pickup_definition.standard_pickup import StandardPickupDefinition
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.layout.base.standard_pickup_state import StandardPickupState


def create_standard_pickup(
    pickup: StandardPickupDefinition,
    state: StandardPickupState,
    resource_database: ResourceDatabase,
    ammo: AmmoPickupDefinition | None,
    ammo_requires_main_item: bool,
) -> PickupEntry:
    """
    Creates a PickupEntry for the given StandardPickup
    :param state:
    :param pickup:
    :param resource_database:
    :param ammo:
    :param ammo_requires_main_item:
    :return:
    """

    extra_resources: list[tuple[ItemResourceInfo, int]] = [
        (resource_database.get_item(ammo_name), ammo_count)
        for ammo_name, ammo_count in zip(pickup.ammo, state.included_ammo, strict=True)
    ]
    extra_resources.extend(
        (resource_database.get_item(item), count) for item, count in pickup.additional_resources.items()
    )

    def _create_resources(base_resource: str) -> tuple[ItemResourceInfo, int]:
        return resource_database.get_item(base_resource), 1

    return PickupEntry(
        name=pickup.name,
        progression=tuple(_create_resources(progression) for progression in pickup.progression),
        extra_resources=tuple(extra_resources),
        model=PickupModel(
            game=resource_database.game_enum,
            name=pickup.model_name,
        ),
        offworld_models=pickup.offworld_models,
        gui_category=pickup.gui_category,
        hint_features=pickup.hint_features,
        unlocks_resource=pickup.unlocks_ammo,
        respects_lock=ammo_requires_main_item,
        resource_lock=ammo.create_resource_lock(resource_database) if ammo is not None else None,
        generator_params=PickupGeneratorParams(
            preferred_location_category=pickup.preferred_location_category,
            probability_offset=pickup.probability_offset,
            probability_multiplier=pickup.probability_multiplier * state.priority,
            index_age_impact=pickup.index_age_impact,
        ),
        show_in_credits_spoiler=pickup.show_in_credits_spoiler,
    )


def create_ammo_pickup(
    ammo: AmmoPickupDefinition,
    ammo_count: Sequence[int],
    requires_main_item: bool,
    resource_database: ResourceDatabase,
) -> PickupEntry:
    """
    Creates a PickupEntry for an expansion of the given ammo.
    :param ammo:
    :param ammo_count:
    :param requires_main_item:
    :param resource_database:
    :return:
    """
    resources = [(resource_database.get_item(item), count) for item, count in zip(ammo.items, ammo_count)]
    resources.extend((resource_database.get_item(item), count) for item, count in ammo.additional_resources.items())

    return PickupEntry(
        name=ammo.name,
        progression=(),
        extra_resources=tuple(resources),
        model=PickupModel(
            game=resource_database.game_enum,
            name=ammo.model_name,
        ),
        offworld_models=ammo.offworld_models,
        gui_category=ammo.gui_category,
        hint_features=ammo.hint_features,
        respects_lock=requires_main_item,
        resource_lock=ammo.create_resource_lock(resource_database),
        generator_params=PickupGeneratorParams(
            preferred_location_category=ammo.preferred_location_category,
            probability_offset=ammo.probability_offset,
            probability_multiplier=ammo.probability_multiplier,
            index_age_impact=ammo.index_age_impact,
        ),
        show_in_credits_spoiler=False,
        is_expansion=True,
    )


def create_generated_pickup(
    pickup_group: str,
    resource_database: ResourceDatabase,
    *,
    minimum_progression: int = 0,
    **format_kwargs: Any,
) -> PickupEntry:
    """
    Creates a concrete PickupEntry given a generated pickup group and an identifier
    :param pickup_group:
    :param resource_database:
    :param minimum_progression:
    :return:
    """

    pickup_database = default_database.pickup_database_for_game(resource_database.game_enum)
    pickup = pickup_database.generated_pickups[pickup_group]

    assert not pickup.ammo
    assert not pickup.unlocks_ammo

    def _create_resources(base_resource: str, count: int = 1) -> tuple[ItemResourceInfo, int]:
        return resource_database.get_item(base_resource.format(**format_kwargs)), count

    return PickupEntry(
        name=pickup.name.format(**format_kwargs),
        progression=tuple(_create_resources(progression) for progression in pickup.progression),
        extra_resources=tuple(_create_resources(item, count) for item, count in pickup.additional_resources.items()),
        model=PickupModel(
            game=resource_database.game_enum,
            name=pickup.model_name.format(**format_kwargs),
        ),
        offworld_models=frozendict(
            {game: model_name.format(**format_kwargs) for game, model_name in pickup.offworld_models.items()}
        ),
        gui_category=pickup.gui_category,
        hint_features=pickup.hint_features,
        generator_params=PickupGeneratorParams(
            preferred_location_category=pickup.preferred_location_category,
            probability_offset=pickup.probability_offset,
            probability_multiplier=pickup.probability_multiplier,
            index_age_impact=pickup.index_age_impact,
            required_progression=minimum_progression,
        ),
    )


USELESS_PICKUP_CATEGORY = hint_features.HintFeature(
    name="useless",
    long_name="Useless",
    hint_details=hint_features.HintDetails("an ", "Energy Transfer Module"),
)


def create_nothing_pickup(resource_database: ResourceDatabase, model_name: str = "Nothing") -> PickupEntry:
    """
    Creates a Nothing pickup.
    :param resource_database:
    :param model_name:
    :return:
    """
    return PickupEntry(
        name="Nothing",
        progression=(),
        model=PickupModel(
            game=resource_database.game_enum,
            name=model_name,
        ),
        gui_category=USELESS_PICKUP_CATEGORY,
        hint_features=frozenset((USELESS_PICKUP_CATEGORY,)),
        generator_params=PickupGeneratorParams(
            preferred_location_category=LocationCategory.MAJOR,  # TODO
        ),
        show_in_credits_spoiler=False,
    )


def create_visual_nothing(game: RandovaniaGame, model_name: str, pickup_name: str = "Unknown item") -> PickupEntry:
    """
    Creates a Nothing pickup that should only be used for visual purposes.
    :param game: The game from where the model comes from.
    :param model_name: The model name for the Nothing pickup.
    :param pickup_name: The name of the Nothing pickup. Defaults to "Unknown item".
    :return:
    """
    return PickupEntry(
        name=pickup_name,
        progression=(),
        model=PickupModel(
            game=game,
            name=model_name,
        ),
        gui_category=USELESS_PICKUP_CATEGORY,
        hint_features=frozenset((USELESS_PICKUP_CATEGORY,)),
        generator_params=PickupGeneratorParams(
            preferred_location_category=LocationCategory.MAJOR,  # TODO
        ),
        show_in_credits_spoiler=False,
    )
