from typing import Dict

import pytest

from randovania.bitpacking.bitpacking import pack_value, BitPackDecoder
from randovania.resolver.pickup_quantities import PickupQuantities


@pytest.fixture(params=[{"Missile Expansion": 0, "Light Suit": 0, "Super Missile": 0},
                        {"Missile Expansion": 0, "Light Suit": 0, "Super Missile": 1},
                        {"Missile Expansion": 10, "Light Suit": 0, "Super Missile": 0},
                        {"Missile Expansion": 10, "Light Suit": 2, "Super Missile": 1},
                        {"Missile Expansion": 10, "Super Missile": 1},
                        ], name="pickup_quantities")
def _pickup_quantities(request):
    yield request.param


def test_compare_encode_round_trip(pickup_quantities: Dict[str, int]):
    original = PickupQuantities.from_params(pickup_quantities)
    encoded = pack_value(original)

    decoded = PickupQuantities.bit_pack_unpack(BitPackDecoder(encoded))
    assert original == decoded
