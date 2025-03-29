from __future__ import annotations

import re
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from frozendict import frozendict

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.game.game_enum import RandovaniaGame
from randovania.game_description.pickup.pickup_definition.standard_pickup import StandardPickupDefinition
from randovania.game_description.pickup.pickup_entry import StartingPickupBehavior
from randovania.game_description.resources.location_category import LocationCategory
from randovania.layout.base.standard_pickup_state import (
    DEFAULT_MAXIMUM_SHUFFLED,
    PRIORITY_LIMITS,
    StandardPickupState,
)

if TYPE_CHECKING:
    import pytest_mock

    from randovania.game_description.pickup.pickup_entry import PickupEntry


@pytest.fixture(
    params=[
        {"encoded": b"\x10", "bit_count": 4, "json": {}},
        {"encoded": b"P", "bit_count": 4, "json": {"num_shuffled_pickups": 1}},
        {"encoded": b"\x81", "bit_count": 8, "json": {"num_shuffled_pickups": 2}},
        {"encoded": b"\x85", "bit_count": 8, "json": {"num_shuffled_pickups": 3}},
        {"encoded": b"\xa2\xca", "bit_count": 15, "json": {"num_shuffled_pickups": 99}},
        {"encoded": b"\x842", "bit_count": 15, "json": {"num_shuffled_pickups": 3, "priority": 2.5}},
        # Energy Tank
        {
            "encoded": b"\x92\x88",
            "bit_count": 13,
            "progression": "EnergyTank",
            "json": {"num_shuffled_pickups": 6, "num_included_in_starting_pickups": 10},
        },
        # Ammo
        {"encoded": b"\x1b\x80", "bit_count": 9, "ammo_index": ("PowerBomb",), "json": {"included_ammo": [7]}},
        {"encoded": b"\x10", "bit_count": 5, "ammo_index": ("DarkAmmo",), "json": {"included_ammo": [0]}},
        {"encoded": b"\x18(", "bit_count": 13, "ammo_index": ("DarkAmmo",), "json": {"included_ammo": [5]}},
        {
            "encoded": b"\x10",
            "bit_count": 5,
            "ammo_index": ("DarkAmmo", "LightAmmo"),
            "json": {"included_ammo": [0, 0]},
        },
        {
            "encoded": b"\x1eX",
            "bit_count": 14,
            "ammo_index": ("DarkAmmo", "LightAmmo"),
            "json": {"included_ammo": [150, 150]},
        },
        {
            "encoded": b"\x1b\x9b ",
            "bit_count": 22,
            "ammo_index": ("DarkAmmo", "LightAmmo"),
            "json": {"included_ammo": [230, 200]},
        },
    ],
)
def standard_pickup_state(request, echoes_pickup_database, generic_pickup_category):
    encoded: bytes = request.param["encoded"]

    pickup = StandardPickupDefinition(
        game=RandovaniaGame.METROID_PRIME_ECHOES,
        name="Item Name",
        gui_category=generic_pickup_category,
        hint_features=frozenset((generic_pickup_category,)),
        model_name="Model Name",
        offworld_models=frozendict(),
        progression=(request.param.get("progression", "Power"),),
        ammo=request.param.get("ammo_index", ()),
        starting_condition=StartingPickupBehavior.MUST_BE_STARTING,
        original_locations=(),
        probability_offset=0.0,
        preferred_location_category=LocationCategory.MAJOR,
    )
    included_ammo = tuple(0 for _ in request.param["json"].get("included_ammo", []))
    reference = StandardPickupState(included_ammo=included_ammo)
    return pickup, encoded, request.param["bit_count"], StandardPickupState.from_json(request.param["json"]), reference


def test_decode(standard_pickup_state):
    # Setup
    pickup, data, _, expected, reference = standard_pickup_state

    # Run
    decoder = BitPackDecoder(data)
    result = StandardPickupState.bit_pack_unpack(decoder, pickup, reference=reference)

    # Assert
    assert result == expected


def test_encode(standard_pickup_state):
    # Setup
    pickup, expected_bytes, expected_bit_count, value, reference = standard_pickup_state

    # Run
    result, bit_count = bitpacking.pack_results_and_bit_count(value.bit_pack_encode(pickup, reference=reference))

    # Assert
    assert bit_count == expected_bit_count
    assert result == expected_bytes


def test_blank_as_json():
    assert StandardPickupState().as_json == {}


def test_blank_from_json():
    assert StandardPickupState.from_json({}) == StandardPickupState()


def _check_consistency(state: StandardPickupState, pickup: PickupEntry, error: str) -> None:
    with pytest.raises(ValueError, match=re.escape(error)):
        state.check_consistency(pickup)


@pytest.mark.parametrize(("amount"), [100, -1])
def test_amount_of_pickups_shuffled(amount: int):
    pickup = MagicMock()
    pickup.game = RandovaniaGame.BLANK
    pickup.name = "Starting Item Surplus"
    pickup.starting_condition = StartingPickupBehavior.CAN_BE_STARTING
    state = StandardPickupState(num_shuffled_pickups=amount)
    expected_error = f"Can only shuffle between 0 and {DEFAULT_MAXIMUM_SHUFFLED[-1]} copies,"
    f" got {state.num_shuffled_pickups}. ({pickup.name})"

    _check_consistency(state, pickup, expected_error)


def test_starting_conditions():
    pickup = MagicMock()
    pickup.game = RandovaniaGame.BLANK
    pickup.name = "Banned Starting Item"
    pickup.starting_condition = StartingPickupBehavior.CAN_NEVER_BE_STARTING
    state = StandardPickupState(num_included_in_starting_pickups=1)
    expected_error = f"{pickup.name} cannot be a starting item."

    _check_consistency(state, pickup, expected_error)

    pickup.name = "Required Starting Item"
    pickup.starting_condition = StartingPickupBehavior.MUST_BE_STARTING
    state = StandardPickupState(num_included_in_starting_pickups=0)
    expected_error = f"Required items must be included in starting items. ({pickup.name})"

    _check_consistency(state, pickup, expected_error)


def test_starting_with_progressives():
    pickup = MagicMock()
    pickup.game = RandovaniaGame.BLANK
    pickup.name = "Progressive Starting Item"
    pickup.starting_conidition = StartingPickupBehavior.CAN_NEVER_BE_STARTING
    pickup.progression = ["Item", "Cooler Item"]
    state = StandardPickupState(num_included_in_starting_pickups=1)
    expected_error = f"Progressive items cannot be starting items. ({pickup.name})"

    _check_consistency(state, pickup, expected_error)


def test_max_item_capacity(mocker: pytest_mock.MockerFixture):
    pickup = MagicMock()
    pickup.game = RandovaniaGame.BLANK
    pickup.name = "Item Over Maximum Capacity"
    pickup_info = MagicMock()
    pickup_info.max_capacity = 1
    pickup.progression = [MagicMock()]
    state = StandardPickupState(num_included_in_starting_pickups=2)
    mocker.patch(
        "randovania.game_description.resources.resource_database.ResourceDatabase.get_item", return_value=pickup_info
    )
    expected_error = f"More starting copies than the item's maximum. ({pickup.name})"

    _check_consistency(state, pickup, expected_error)


def test_vanilla_pickup_locations():
    pickup = MagicMock()
    pickup.game = RandovaniaGame.BLANK
    pickup.name = "Item to be placed in vanilla location"
    pickup.original_locations = False
    pickup.starting_condition = StartingPickupBehavior.CAN_BE_STARTING
    state = StandardPickupState(include_copy_in_original_location=True)
    expected_error = f"No vanilla location defined. ({pickup.name})"

    _check_consistency(state, pickup, expected_error)


@pytest.mark.parametrize(("priority"), [11.0, -1.0])
def test_pickup_priority_range(priority: float):
    pickup = MagicMock()
    pickup.game = RandovaniaGame.BLANK
    pickup.name = "Item with broken priority"
    state = StandardPickupState(priority=priority)
    expected_error = "Priority must be between {min} and {max}, got {priority}".format(
        priority=state.priority,
        **PRIORITY_LIMITS,
    )

    _check_consistency(state, pickup, expected_error)


def test_ammo_config(mocker: pytest_mock.MockerFixture):
    # Check ammo array
    pickup = MagicMock()
    pickup.game = RandovaniaGame.BLANK
    pickup.name = "Item with extra ammo entry"
    pickup.ammo = ["Dark Ammo", "Light Ammo"]
    state = StandardPickupState(included_ammo=[2])
    expected_error = f"Mismatched included_ammo array size. ({pickup.name})"

    _check_consistency(state, pickup, expected_error)

    # Check correct ammo amounts
    pickup.name = "Item over ammo limit"
    pickup.ammo = ["Dark Ammo"]
    ammo_name = "Dark Ammo"
    ammo = 5
    state = StandardPickupState(included_ammo=[5])
    pickup_info = MagicMock()
    pickup_info.max_capacity = 1
    fake_get_item = mocker.patch(
        "randovania.game_description.resources.resource_database.ResourceDatabase.get_item", return_value=pickup_info
    )
    expected_error = f"Including more than maximum capacity for ammo {ammo_name}."
    f" Included: {ammo}; Max: {fake_get_item(ammo_name).max_capacity}"

    _check_consistency(state, pickup, expected_error)
