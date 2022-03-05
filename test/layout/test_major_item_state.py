import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.game_description.item.major_item import MajorItem
from randovania.games.game import RandovaniaGame
from randovania.layout.base.major_item_state import MajorItemState


@pytest.fixture(
    params=[
        {"encoded": b'\x10', "bit_count": 4, "json": {}},
        {"encoded": b'P', "bit_count": 4, "json": {"num_shuffled_pickups": 1}},
        {"encoded": b'\x81', "bit_count": 8, "json": {"num_shuffled_pickups": 2}},
        {"encoded": b'\x85', "bit_count": 8, "json": {"num_shuffled_pickups": 3}},
        {"encoded": b'\xa2\xca', "bit_count": 15, "json": {"num_shuffled_pickups": 99}},
        {"encoded": b'\x842', "bit_count": 15, "json": {"num_shuffled_pickups": 3, "priority": 2.5}},

        # Energy Tank
        {"encoded": b'\x92\x88', "bit_count": 13, "progression": "EnergyTank", "json": {"num_shuffled_pickups": 6,
                                                                                        "num_included_in_starting_items": 10}},

        # Ammo
        {"encoded": b'\x1b\x80', "bit_count": 9, "ammo_index": ("PowerBomb",), "json": {"included_ammo": [7]}},
        {"encoded": b'\x10', "bit_count": 5, "ammo_index": ("DarkAmmo",), "json": {"included_ammo": [0]}},
        {"encoded": b'\x18(', "bit_count": 13, "ammo_index": ("DarkAmmo",), "json": {"included_ammo": [5]}},
        {"encoded": b'\x10', "bit_count": 5, "ammo_index": ("DarkAmmo", "LightAmmo"),
         "json": {"included_ammo": [0, 0]}},
        {"encoded": b'\x1eX', "bit_count": 14, "ammo_index": ("DarkAmmo", "LightAmmo"),
         "json": {"included_ammo": [150, 150]}},
        {"encoded": b'\x1b\x9b ', "bit_count": 22, "ammo_index": ("DarkAmmo", "LightAmmo"),
         "json": {"included_ammo": [230, 200]}},
    ],
    name="major_item_state")
def _major_item_state(request, echoes_item_database, generic_item_category):
    encoded: bytes = request.param["encoded"]

    item = MajorItem(
        game=RandovaniaGame.METROID_PRIME_ECHOES,
        name="Item Name",
        item_category=generic_item_category,
        broad_category=generic_item_category,
        model_name="Model Name",
        progression=(request.param.get("progression", "Power"),),
        default_starting_count=0,
        default_shuffled_count=1,
        ammo_index=request.param.get("ammo_index", ()),
        must_be_starting=True,
        original_index=None,
        probability_offset=0,
    )
    included_ammo = tuple(0 for _ in request.param["json"].get("included_ammo", []))
    reference = MajorItemState(included_ammo=included_ammo)
    return item, encoded, request.param["bit_count"], MajorItemState.from_json(request.param["json"]), reference


def test_decode(major_item_state):
    # Setup
    item, data, _, expected, reference = major_item_state

    # Run
    decoder = BitPackDecoder(data)
    result = MajorItemState.bit_pack_unpack(decoder, item, reference=reference)

    # Assert
    assert result == expected


def test_encode(major_item_state):
    # Setup
    item, expected_bytes, expected_bit_count, value, reference = major_item_state

    # Run
    result, bit_count = bitpacking.pack_results_and_bit_count(value.bit_pack_encode(item, reference=reference))

    # Assert
    assert bit_count == expected_bit_count
    assert result == expected_bytes


def test_blank_as_json():
    assert MajorItemState().as_json == {}


def test_blank_from_json():
    assert MajorItemState.from_json({}) == MajorItemState()
