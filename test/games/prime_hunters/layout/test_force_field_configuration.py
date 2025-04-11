from __future__ import annotations

import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.games.prime_hunters.layout.force_field_configuration import ForceFieldConfiguration


@pytest.fixture(
    params=[
        {"encoded": b"\x00", "bit_count": 2, "json": {"force_field_requirement": {}}},
        {"encoded": b"\x00", "bit_count": 2, "json": ForceFieldConfiguration.default().with_vanilla().as_json},
        {"encoded": b"@", "bit_count": 2, "json": ForceFieldConfiguration.default().with_full_random().as_json},
        {
            "encoded": b"\x86\x1d\xdd\xc4DUY\x99\x95UT\xcc\xcc",
            "bit_count": 102,
            "json": {
                "force_field_requirement": {"Celestial Archives/Celestial Gateway/Battlehammer Force Field": "random"}
            },
        },
    ],
)
def force_field_data(request):
    return (
        request.param["encoded"],
        request.param["bit_count"],
        ForceFieldConfiguration.from_json(request.param["json"]),
    )


def test_decode(force_field_data):
    # Setup
    data, _, expected = force_field_data

    # Run
    decoder = BitPackDecoder(data)
    result = ForceFieldConfiguration.bit_pack_unpack(decoder, {})

    # Assert
    assert result == expected


def test_encode(force_field_data):
    # Setup
    expected_bytes, expected_bit_count, value = force_field_data

    # Run
    result, bit_count = bitpacking.pack_results_and_bit_count(value.bit_pack_encode({}))

    # Assert
    assert result == expected_bytes
    assert bit_count == expected_bit_count


def test_blank_from_json():
    blank = ForceFieldConfiguration.from_json({"force_field_requirement": {}})
    assert blank.as_json == {
        "force_field_requirement": {
            "Celestial Archives/Celestial Gateway/Battlehammer Force Field": "battlehammer",
            "Celestial Archives/Incubation Vault 01/Shock Coil Force Field": "shock-coil",
            "Celestial Archives/Incubation Vault 02/Shock Coil Force Field": "shock-coil",
            "Celestial Archives/Incubation Vault 03/Shock Coil Force Field (Upper)": "shock-coil",
            "Celestial Archives/Incubation Vault 03/Shock Coil Force Field (Lower)": "shock-coil",
            "Celestial Archives/Synergy Core/Volt Driver Force Field": "volt-driver",
            "Alinos/Alinos Perch/Magmaul Force Field": "magmaul",
            "Alinos/Council Chamber/Magmaul Force Field (Entrance)": "magmaul",
            "Alinos/Council Chamber/Magmaul Force Field (Jump Pad)": "magmaul",
            "Alinos/Council Chamber/Magmaul Force Field (Upper)": "magmaul",
            "Alinos/High Ground/Volt Driver Force Field (East)": "volt-driver",
            "Alinos/High Ground/Volt Driver Force Field (North)": "volt-driver",
            "Alinos/High Ground/Volt Driver Force Field (South)": "volt-driver",
            "Alinos/High Ground/Volt Driver Force Field (Upper)": "volt-driver",
            "Alinos/High Ground/Judicator Force Field (Lower)": "judicator",
            "Alinos/High Ground/Judicator Force Field (Upper)": "judicator",
            "Arcterra/Ice Hive/Judicator Force Field (Entrance)": "judicator",
            "Arcterra/Ice Hive/Judicator Force Field (War Wasps)": "judicator",
            "Arcterra/Ice Hive/Judicator Force Field (Judicator Room)": "judicator",
            "Arcterra/Ice Hive/Judicator Force Field (Bridge)": "judicator",
            "Arcterra/Ice Hive/Judicator Force Field (Alcove)": "judicator",
            "Vesper Defense Outpost/Compression Chamber/Battlehammer Force Field (Left)": "battlehammer",
            "Vesper Defense Outpost/Compression Chamber/Battlehammer Force Field (Right)": "battlehammer",
            "Vesper Defense Outpost/Cortex CPU/Battlehammer Force Field": "battlehammer",
            "Vesper Defense Outpost/Weapons Complex/Battlehammer Force Field": "battlehammer",
        }
    }
