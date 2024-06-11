from __future__ import annotations

import pytest
from frozendict import frozendict

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.game_description.pickup.standard_pickup import StandardPickupDefinition
from randovania.game_description.resources.location_category import LocationCategory
from randovania.games.game import RandovaniaGame
from randovania.layout.base.standard_pickup_state import StandardPickupState


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
        pickup_category=generic_pickup_category,
        broad_category=generic_pickup_category,
        model_name="Model Name",
        offworld_models=frozendict(),
        progression=(request.param.get("progression", "Power"),),
        ammo=request.param.get("ammo_index", ()),
        must_be_starting=True,
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
