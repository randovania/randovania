import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.game_description.item.major_item import MajorItem
from randovania.games.game import RandovaniaGame
from randovania.layout.base.major_item_state import MajorItemState


@pytest.fixture(
    params=[
        {"encoded": b'\x00', "bit_count": 3, "json": {}},
        {"encoded": b'@', "bit_count": 3, "json": {"num_shuffled_pickups": 1}},
        {"encoded": b'\x80', "bit_count": 7, "json": {"num_shuffled_pickups": 2}},
        {"encoded": b'\x84', "bit_count": 7, "json": {"num_shuffled_pickups": 3}},
        {"encoded": b'\xa2\xc8', "bit_count": 14, "json": {"num_shuffled_pickups": 99}},

        # Energy Tank
        {"encoded": b'\x92\x80', "bit_count": 12, "progression": 42, "json": {"num_shuffled_pickups": 6,
                                                                        "num_included_in_starting_items": 10}},

        # Ammo
        {"encoded": b'\x17', "bit_count": 8, "ammo_index": (43,), "json": {"included_ammo": [7]}},
        {"encoded": b'\x00', "bit_count": 4, "ammo_index": (45,), "json": {"included_ammo": [0]}},
        {"encoded": b'\x10P', "bit_count": 12, "ammo_index": (45,), "json": {"included_ammo": [5]}},
        {"encoded": b'\x00', "bit_count": 4, "ammo_index": (45, 46), "json": {"included_ammo": [0, 0]}},
        {"encoded": b'\x1c\xb0', "bit_count": 13, "ammo_index": (45, 46), "json": {"included_ammo": [150, 150]}},
        {"encoded": b'\x176@', "bit_count": 21, "ammo_index": (45, 46), "json": {"included_ammo": [230, 200]}},
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
        progression=(request.param.get("progression", 0),),
        ammo_index=request.param.get("ammo_index", ()),
        required=True,
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
