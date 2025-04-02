from __future__ import annotations

import typing
from typing import TypeVar

import pytest
from frozendict import frozendict

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.layout.base.hint_configuration import HintConfiguration, SpecificPickupHintMode

T = TypeVar("T")


@pytest.fixture(
    params=[
        {
            "encoded": b"L\x00",
            "sky_temple_keys": SpecificPickupHintMode.DISABLED.value,
        },
        {
            "encoded": b"\\\x00",
            "sky_temple_keys": SpecificPickupHintMode.HIDE_AREA.value,
        },
        {
            "encoded": b"0",
            "sky_temple_keys": SpecificPickupHintMode.PRECISE.value,
        },
    ],
)
def hint_config_with_data(request, default_echoes_configuration):
    data = typing.cast("dict", default_echoes_configuration.hints.as_json)
    reference = HintConfiguration.from_json(data)
    specific_pickup = dict(data["specific_pickup_hints"])
    specific_pickup["sky_temple_keys"] = request.param["sky_temple_keys"]
    data["specific_pickup_hints"] = frozendict(specific_pickup)

    return (
        typing.cast("bytes", request.param["encoded"]),
        HintConfiguration.from_json(data),
        data,
        reference,
    )


def test_decode(hint_config_with_data):
    # Setup
    data, expected, _, reference = hint_config_with_data

    # Run
    decoder = BitPackDecoder(data)
    result = HintConfiguration.bit_pack_unpack(decoder, {"reference": reference})

    # Assert
    assert result == expected


def test_encode(hint_config_with_data):
    # Setup
    expected, value, expected_json, reference = hint_config_with_data

    # Run
    result = bitpacking.pack_value(value, {"reference": reference})
    as_json = value.as_json

    # Assert
    assert result == expected
    assert as_json == expected_json
