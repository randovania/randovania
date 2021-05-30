import dataclasses
import uuid
from unittest.mock import patch, MagicMock, ANY

import pytest

from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.layout.prime2.echoes_configuration import LayoutSkyTempleKeyMode
from randovania.layout.permalink import Permalink
from randovania.layout.preset import Preset


@patch("randovania.layout.preset._dictionary_byte_hash", autospec=True)
def test_encode(mock_dictionary_byte_hash: MagicMock, default_preset):
    # Setup
    mock_dictionary_byte_hash.return_value = 120
    link = Permalink(
        seed_number=1000,
        spoiler=True,
        presets={0: default_preset},
    )

    # Run
    encoded = link.as_base64_str

    # Assert
    mock_dictionary_byte_hash.assert_called_once_with(default_preset.configuration.game_data)
    assert encoded == "wDhwJfQnUIg4"


@pytest.mark.parametrize("invalid", [
    "",
    "a",
    "x",
    "zz",
    "AAAAfRxALWmCI50gIQD",
    "AAAAfRxALxmCI50gIQDy"
])
def test_decode_invalid(invalid: str):
    with pytest.raises(ValueError):
        Permalink.from_str(invalid)


@pytest.mark.parametrize("spoiler", [False, True])
@pytest.mark.parametrize("layout", [
    {},
    {
        "sky_temple_keys": LayoutSkyTempleKeyMode.ALL_GUARDIANS,
    },
    {
        "menu_mod": True,
        "warp_to_start": False,
    },
])
def test_round_trip(spoiler: bool,
                    layout: dict,
                    default_preset,
                    mocker):
    # Setup
    random_uuid = uuid.uuid4()
    mocker.patch("uuid.uuid4", return_value=random_uuid)

    preset = Preset(
        name="{} Custom".format(default_preset.name),
        description="A customized preset.",
        uuid=random_uuid,
        base_preset_uuid=default_preset.uuid,
        game=default_preset.game,
        configuration=dataclasses.replace(default_preset.configuration, **layout),
    )

    link = Permalink(
        seed_number=1000,
        spoiler=spoiler,
        presets={0: preset},
    )

    # Run
    after = Permalink.from_str(link.as_base64_str)

    # Assert
    assert link == after


@pytest.mark.parametrize(["permalink", "version"], [
    ("AAAAfR5QLERzIpgS4ICCAHw=", 0),
    ("EAAAfReObArRHMClxLYgIIA+", 1),
    ("MAAAfReKeBWiOYFLiWxAQQDk", 3),
])
def test_decode_old_version(permalink: str, version: int):
    with pytest.raises(ValueError) as exp:
        Permalink.from_str(permalink)
    assert str(exp.value) == ("Given permalink has version {}, but this Randovania "
                              "support only permalink of version {}.".format(version, Permalink.current_version()))


@patch("randovania.layout.preset._dictionary_byte_hash", autospec=True)
def test_decode(mock_dictionary_byte_hash: MagicMock, default_preset):
    mock_dictionary_byte_hash.return_value = 120
    # We're mocking the database hash to avoid breaking tests every single time we change the database

    # This test should break whenever we change how permalinks are created
    # When this happens, we must bump the permalink version and change the tests
    encoded = "wDhwJfQnUIg4"

    expected = Permalink(
        seed_number=1000,
        spoiler=True,
        presets={0: default_preset},
    )

    # Uncomment this line to quickly get the new encoded permalink
    # assert expected.as_base64_str == ""
    # print(expected.as_base64_str)

    # Run
    link = Permalink.from_str(encoded)

    # Assert
    assert link == expected


@pytest.mark.parametrize(["encoded", "num_players"], [
    ("wIQICSSUQJyE", 1),
    ("wGPGpqTvUuEYe95j", 2),
    ("wH369AyR7prkZeJ9", 10),
])
def test_decode_mock_other(encoded, num_players, mocker):
    preset = MagicMock()

    def read_values(decoder: BitPackDecoder, metadata):
        decoder.decode(100, 100)
        return preset

    mock_preset_unpack: MagicMock = mocker.patch("randovania.layout.preset.Preset.bit_pack_unpack",
                                                 side_effect=read_values)

    expected = Permalink(
        seed_number=1000,
        spoiler=True,
        presets={i: preset for i in range(num_players)},
    )
    preset.bit_pack_encode.return_value = [(0, 100), (5, 100)]

    # Uncomment this line to quickly get the new encoded permalink
    # assert expected.as_base64_str == ""
    # print(expected.as_base64_str)

    # Run
    round_trip = expected.as_base64_str
    link = Permalink.from_str(encoded)

    # Assert
    assert link == expected
    assert round_trip == encoded
    mock_preset_unpack.assert_called_once_with(ANY, {"manager": ANY})


@patch("randovania.layout.permalink.Permalink.bit_pack_encode", autospec=True)
def test_permalink_as_str_caches(mock_bit_pack_encode: MagicMock,
                                 default_preset):
    # Setup
    mock_bit_pack_encode.return_value = []
    link = Permalink(
        seed_number=1000,
        spoiler=True,
        presets={0: default_preset},
    )

    # Run
    str1 = link.as_base64_str
    str2 = link.as_base64_str

    # Assert
    assert str1 == "AMXF"
    assert str1 == str2
    assert object.__getattribute__(link, "__cached_as_bytes") is not None
    mock_bit_pack_encode.assert_called_once_with(link, {})
