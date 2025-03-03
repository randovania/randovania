from __future__ import annotations

import dataclasses

import pytest
from frozendict import frozendict

from randovania.game_description.hint_features import HintDetails, HintFeature
from randovania.game_description.pickup.pickup_definition.ammo_pickup import AmmoPickupDefinition
from randovania.game_description.pickup.pickup_definition.standard_pickup import StandardPickupDefinition
from randovania.game_description.pickup.pickup_entry import (
    PickupEntry,
    PickupGeneratorParams,
    PickupModel,
    ResourceLock,
)
from randovania.game_description.resources.location_category import LocationCategory
from randovania.game_description.resources.resource_collection import ResourceCollection
from randovania.games.prime2.patcher import echoes_items
from randovania.generator.pickup_pool import pickup_creator
from randovania.layout.base.standard_pickup_state import StandardPickupState


@pytest.fixture
def less_generic_pickup_category() -> HintFeature:
    return HintFeature(
        name="the_category",
        long_name="The Category",
        hint_details=HintDetails("a ", " wonderful item"),
    )


@pytest.fixture
def echoes_standard_pickup(
    echoes_resource_database, generic_pickup_category, less_generic_pickup_category
) -> StandardPickupDefinition:
    return StandardPickupDefinition(
        game=echoes_resource_database.game_enum,
        name="The Item",
        gui_category=less_generic_pickup_category,
        hint_features=frozenset(
            (
                generic_pickup_category,
                less_generic_pickup_category,
            )
        ),
        model_name="SuperModel",
        offworld_models=frozendict({}),
        progression=("DarkVisor", "MorphBall", "Bombs"),
        ammo=("EnergyTank", "DarkAmmo"),
        must_be_starting=False,
        original_locations=(),
        probability_offset=5.0,
        preferred_location_category=LocationCategory.MAJOR,
    )


@pytest.fixture
def echoes_ammo_pickup(echoes_resource_database, useless_pickup_category, ammo_pickup_category) -> AmmoPickupDefinition:
    return AmmoPickupDefinition(
        game=echoes_resource_database.game_enum,
        name="The Item",
        items=("Missile",),
        gui_category=ammo_pickup_category,
        hint_features=frozenset(
            (
                useless_pickup_category,
                ammo_pickup_category,
            )
        ),
        unlocked_by="MissileLauncher",
        temporary="Temporary1",
        model_name="AmmoModel",
        offworld_models=frozendict({}),
        preferred_location_category=LocationCategory.MINOR,
    )


def test_create_pickup_for(
    echoes_resource_database, generic_pickup_category, echoes_standard_pickup, less_generic_pickup_category
):
    # Setup
    item_a = echoes_resource_database.get_item("DarkVisor")
    item_b = echoes_resource_database.get_item("MorphBall")
    item_c = echoes_resource_database.get_item("Bombs")
    ammo_a = echoes_resource_database.get_item("EnergyTank")
    ammo_b = echoes_resource_database.get_item("DarkAmmo")

    state = StandardPickupState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=0,
        num_included_in_starting_pickups=0,
        included_ammo=(10, 20),
    )

    extra_resources = (
        (ammo_a, 10),
        (ammo_b, 20),
    )

    # Run
    result = pickup_creator.create_standard_pickup(echoes_standard_pickup, state, echoes_resource_database, None, False)

    # Assert
    assert result == PickupEntry(
        name="The Item",
        model=PickupModel(echoes_resource_database.game_enum, "SuperModel"),
        progression=(
            (item_a, 1),
            (item_b, 1),
            (item_c, 1),
        ),
        extra_resources=extra_resources,
        gui_category=less_generic_pickup_category,
        hint_features=frozenset(
            (
                generic_pickup_category,
                less_generic_pickup_category,
            )
        ),
        respects_lock=False,
        generator_params=PickupGeneratorParams(
            preferred_location_category=LocationCategory.MAJOR,
            probability_offset=5.0,
        ),
    )


@pytest.mark.parametrize(
    "ammo_quantity",
    [
        0,
        10,
        15,
    ],
)
def test_create_missile_launcher(
    ammo_quantity: int, echoes_pickup_database, echoes_resource_database, default_generator_params
):
    # Setup
    missile = echoes_resource_database.get_item("Missile")
    missile_launcher = echoes_resource_database.get_item("MissileLauncher")
    temporary = echoes_resource_database.get_item("Temporary1")

    state = StandardPickupState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=0,
        num_included_in_starting_pickups=0,
        included_ammo=(ammo_quantity,),
    )

    # Run
    result = pickup_creator.create_standard_pickup(
        echoes_pickup_database.standard_pickups["Missile Launcher"],
        state,
        echoes_resource_database,
        echoes_pickup_database.ammo_pickups["Missile Expansion"],
        ammo_requires_main_item=True,
    )
    result = dataclasses.replace(result, offworld_models=frozendict({}))
    categories = echoes_pickup_database.pickup_categories

    # Assert
    assert result == PickupEntry(
        name="Missile Launcher",
        progression=((missile_launcher, 1),),
        extra_resources=(
            (missile, ammo_quantity),
            (echoes_resource_database.get_item(echoes_items.PERCENTAGE), 1),
        ),
        model=PickupModel(echoes_resource_database.game_enum, "MissileLauncher"),
        gui_category=categories["missile"],
        hint_features=frozenset(
            (
                categories["major"],
                categories["missile"],
                categories["missile_related"],
                categories["chozo"],
            )
        ),
        generator_params=default_generator_params,
        resource_lock=ResourceLock(
            locked_by=missile_launcher,
            temporary_item=temporary,
            item_to_lock=missile,
        ),
        unlocks_resource=True,
    )


@pytest.mark.parametrize("ammo_quantity", [0, 10, 15])
@pytest.mark.parametrize("ammo_requires_main_item", [False, True])
def test_create_seeker_launcher(
    ammo_quantity: int,
    ammo_requires_main_item: bool,
    echoes_pickup_database,
    echoes_resource_database,
    default_generator_params,
):
    # Setup
    missile = echoes_resource_database.get_item("Missile")
    missile_launcher = echoes_resource_database.get_item("MissileLauncher")
    seeker_launcher = echoes_resource_database.get_item("Seekers")
    temporary = echoes_resource_database.get_item("Temporary1")

    state = StandardPickupState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=0,
        num_included_in_starting_pickups=0,
        included_ammo=(ammo_quantity,),
    )

    # Run
    result = pickup_creator.create_standard_pickup(
        echoes_pickup_database.standard_pickups["Seeker Launcher"],
        state,
        echoes_resource_database,
        echoes_pickup_database.ammo_pickups["Missile Expansion"],
        ammo_requires_main_item,
    )
    result = dataclasses.replace(result, offworld_models=frozendict({}))
    categories = echoes_pickup_database.pickup_categories

    # Assert

    assert result == PickupEntry(
        name="Seeker Launcher",
        progression=((seeker_launcher, 1),),
        extra_resources=(
            (missile, ammo_quantity),
            (echoes_resource_database.get_item(echoes_items.PERCENTAGE), 1),
        ),
        model=PickupModel(echoes_resource_database.game_enum, "SeekerLauncher"),
        gui_category=categories["missile"],
        hint_features=frozenset(
            (
                categories["missile"],
                categories["missile_related"],
                categories["major"],
                categories["luminoth"],
            )
        ),
        respects_lock=ammo_requires_main_item,
        resource_lock=ResourceLock(
            locked_by=missile_launcher,
            temporary_item=temporary,
            item_to_lock=missile,
        ),
        generator_params=default_generator_params,
    )


@pytest.mark.parametrize("requires_main_item", [False, True])
def test_create_ammo_expansion(
    requires_main_item: bool,
    ammo_pickup_category,
    useless_pickup_category,
    echoes_resource_database,
    echoes_ammo_pickup,
):
    # Setup
    primary_a = echoes_resource_database.get_item("MissileLauncher")
    ammo_a = echoes_resource_database.get_item("Missile")
    temporary_a = echoes_resource_database.get_item("Temporary1")

    ammo_count = (11, 150)

    # Run
    result = pickup_creator.create_ammo_pickup(
        echoes_ammo_pickup, ammo_count, requires_main_item, echoes_resource_database
    )

    # Assert
    assert result == PickupEntry(
        name="The Item",
        model=PickupModel(echoes_resource_database.game_enum, "AmmoModel"),
        progression=(),
        extra_resources=((ammo_a, ammo_count[0]),),
        gui_category=ammo_pickup_category,
        hint_features=frozenset(
            (
                useless_pickup_category,
                ammo_pickup_category,
            )
        ),
        respects_lock=requires_main_item,
        resource_lock=ResourceLock(
            locked_by=primary_a,
            temporary_item=temporary_a,
            item_to_lock=ammo_a,
        ),
        generator_params=PickupGeneratorParams(
            preferred_location_category=LocationCategory.MINOR,
            probability_offset=0.0,
            probability_multiplier=2.0,
            index_age_impact=1.0,
        ),
        show_in_credits_spoiler=False,
        is_expansion=True,
    )


@pytest.mark.parametrize("include_before", [False, True])
def test_missile_expansion_before_launcher(include_before, echoes_pickup_database, echoes_resource_database):
    # Setup
    ammo = echoes_pickup_database.ammo_pickups["Missile Expansion"]
    standard_pickup = echoes_pickup_database.standard_pickups["Missile Launcher"]

    missile = echoes_resource_database.get_item(ammo.items[0])
    missile_launcher = echoes_resource_database.get_item(standard_pickup.progression[0])
    temporary = echoes_resource_database.get_item(ammo.temporary)
    percent = echoes_resource_database.get_item(echoes_items.PERCENTAGE)

    # Run
    expansion = pickup_creator.create_ammo_pickup(ammo, [5], True, echoes_resource_database)
    launcher = pickup_creator.create_standard_pickup(
        standard_pickup, StandardPickupState(included_ammo=(5,)), echoes_resource_database, ammo, True
    )

    def to_dict(col: ResourceCollection):
        return dict(col.as_resource_gain())

    collection = ResourceCollection.with_database(echoes_resource_database)

    if include_before:
        # Ammo Expansion
        collection.add_resource_gain(expansion.resource_gain(collection, force_lock=True))
        assert to_dict(collection) == {percent: 1, temporary: 5}

    # Add Launcher
    collection.add_resource_gain(launcher.resource_gain(collection, force_lock=True))
    if include_before:
        assert to_dict(collection) == {percent: 2, temporary: 0, missile_launcher: 1, missile: 10}
    else:
        assert to_dict(collection) == {percent: 1, temporary: 0, missile_launcher: 1, missile: 5}

    # Ammo Expansion
    collection.add_resource_gain(expansion.resource_gain(collection, force_lock=True))
    if include_before:
        assert to_dict(collection) == {percent: 3, temporary: 0, missile_launcher: 1, missile: 15}
    else:
        assert to_dict(collection) == {percent: 2, temporary: 0, missile_launcher: 1, missile: 10}


@pytest.mark.parametrize(
    ("changes", "error"),
    [
        (
            {
                "progression": (),
                "ammo": (),
            },
            "Standard Pickup The Item has no progression nor ammo.",
        ),
        ({"custom_count_for_shuffled_case": 0}, "Standard Pickup The Item count for shuffled case is less than 1."),
        ({"custom_count_for_starting_case": 0}, "Standard Pickup The Item count for starting case is less than 1."),
    ],
)
def test_standard_pickup_definition_invalid(changes: dict, error: str, echoes_standard_pickup):
    with pytest.raises(ValueError, match=error):
        dataclasses.replace(echoes_standard_pickup, **changes)


@pytest.mark.parametrize(("value", "shuffled_expected", "starting_expected"), [(None, 3, 1), (2, 2, 2)])
def test_standard_pickup_definition_case_counts(
    value: int | None, shuffled_expected: int, starting_expected: int, echoes_standard_pickup
):
    pickup = dataclasses.replace(
        echoes_standard_pickup,
        custom_count_for_shuffled_case=value,
        custom_count_for_starting_case=value,
    )

    assert pickup.count_for_shuffled_case == shuffled_expected
    assert pickup.count_for_starting_case == starting_expected


@pytest.mark.parametrize(
    ("changes", "error"),
    [
        (
            {
                "unlocked_by": None,
            },
            "If temporary is set, unlocked_by must be set.",
        ),
        ({"items": ("Missile", "DarkAmmo")}, "If temporary is set, only one item is supported. Got 2 instead"),
        (
            {
                "temporary": None,
            },
            "If temporary is not set, unlocked_by must not be set.",
        ),
    ],
)
def test_ammo_pickup_definition_invalid(changes: dict, error: str, echoes_ammo_pickup):
    with pytest.raises(ValueError, match=error):
        dataclasses.replace(echoes_ammo_pickup, **changes)


def test_standard_pickup_as_json(echoes_standard_pickup):
    json_data = echoes_standard_pickup.as_json
    assert json_data == {
        "gui_category": "the_category",
        "hint_features": ["generic", "the_category"],
        "model_name": "SuperModel",
        "offworld_models": frozendict(),
        "preferred_location_category": "major",
        "probability_offset": 5.0,
        "progression": ["DarkVisor", "MorphBall", "Bombs"],
        "ammo": ["EnergyTank", "DarkAmmo"],
        "expected_case_for_describer": "shuffled",
    }


def test_ammo_pickup_as_json(echoes_ammo_pickup):
    json_data = echoes_ammo_pickup.as_json
    assert json_data == {
        "gui_category": "expansion",
        "hint_features": ["expansion", "useless"],
        "model_name": "AmmoModel",
        "offworld_models": frozendict(),
        "preferred_location_category": "minor",
        "items": ["Missile"],
        "unlocked_by": "MissileLauncher",
        "temporary": "Temporary1",
    }
