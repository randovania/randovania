import contextlib
import dataclasses
import uuid
from unittest.mock import patch, MagicMock, ANY, call

import pytest

from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.games.game import RandovaniaGame
from randovania.games.prime2.layout.echoes_configuration import LayoutSkyTempleKeyMode
from randovania.layout.generator_parameters import GeneratorParameters
from randovania.layout.preset import Preset


def test_invalid_seed_range(default_blank_preset):
    with pytest.raises(ValueError, match="Invalid seed number: -1"):
        GeneratorParameters(
            seed_number=-1,
            spoiler=False,
            presets=[default_blank_preset],
        )


def test_no_race_and_develop(default_blank_preset):
    with pytest.raises(ValueError, match="Race permalinks can't have development enabled"):
        GeneratorParameters(
            seed_number=1000,
            spoiler=False,
            development=True,
            presets=[default_blank_preset],
        )


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
                    default_echoes_preset,
                    mocker):
    # Setup
    random_uuid = uuid.uuid4()
    mocker.patch("uuid.uuid4", return_value=random_uuid)

    preset = Preset(
        name=f"{default_echoes_preset.game.long_name} Custom",
        description="A customized preset.",
        uuid=random_uuid,
        game=default_echoes_preset.game,
        configuration=dataclasses.replace(default_echoes_preset.configuration, **layout),
    )

    params = GeneratorParameters(
        seed_number=1000,
        spoiler=spoiler,
        presets=[preset],
    )

    # Run
    after = GeneratorParameters.from_bytes(params.as_bytes)

    # Assert
    assert params == after


@pytest.mark.parametrize("development", [False, True])
@pytest.mark.parametrize("extra_data", [False, True])
def test_decode(default_blank_preset, mocker, development, extra_data):
    # We're mocking the database hash to avoid breaking tests every single time we change the database
    mocker.patch("randovania.layout.generator_parameters.game_db_hash", autospec=True,
                 return_value=120)

    random_uuid = uuid.uuid4()
    mocker.patch("uuid.uuid4", return_value=random_uuid)

    # This test should break whenever we change how permalinks are created
    # When this happens, we must bump the permalink version and change the tests
    if development:
        encoded = b'8\x00\x00\x1fF\x00\x00'
    else:
        encoded = b'8\x00\x00\x1fD\x00\x03\xc0'
    if extra_data:
        encoded += b"="

    expected = GeneratorParameters(
        seed_number=1000,
        spoiler=True,
        presets=[dataclasses.replace(
            default_blank_preset,
            name=f"{default_blank_preset.game.long_name} Custom",
            description="A customized preset.",
            uuid=random_uuid,
        )],
        development=development,
    )

    # Uncomment this line to quickly get the new encoded permalink
    # assert expected.as_bytes == b""
    # print(expected.as_bytes)

    # Run
    if extra_data:
        expectation = pytest.raises(ValueError)
    else:
        expectation = contextlib.nullcontext()

    with expectation:
        link = GeneratorParameters.from_bytes(encoded)

    # Assert
    if not extra_data:
        assert link == expected


@pytest.mark.parametrize(["encoded", "num_players"], [
    (b'$\x00\x00\x1fD\x00+\xc0', 1),
    (b'D\x80\x00\x03\xe8\x80\x05\x00\x15\xe0', 2),
    (b'\x8cI$\x92H\x00\x00>\x88\x00P\x01@\x05\x00\x14\x00P\x01@\x05\x00\x14\x00P\x01^\x00', 10),
])
def test_decode_mock_other(encoded, num_players, mocker):
    # We're mocking the database hash to avoid breaking tests every single time we change the database
    mocker.patch("randovania.layout.generator_parameters.game_db_hash", autospec=True,
                 return_value=120)

    preset = MagicMock()
    preset.game = RandovaniaGame.METROID_PRIME_ECHOES

    def read_values(decoder: BitPackDecoder, metadata):
        decoder.decode(100, 100)
        return preset

    mock_preset_unpack: MagicMock = mocker.patch("randovania.layout.preset.Preset.bit_pack_unpack",
                                                 side_effect=read_values)

    expected = GeneratorParameters(
        seed_number=1000,
        spoiler=True,
        presets=[preset] * num_players,
    )
    preset.bit_pack_encode.return_value = [(0, 100), (5, 100)]

    # Uncomment this line to quickly get the new encoded permalink
    # print(expected.as_bytes)
    # assert expected.as_bytes == b""

    # Run
    round_trip = expected.as_bytes
    link = GeneratorParameters.from_bytes(encoded)

    # Assert
    assert link == expected
    assert round_trip == encoded
    mock_preset_unpack.assert_has_calls([
        call(ANY, {"manager": ANY, "game": RandovaniaGame.METROID_PRIME_ECHOES})
        for _ in range(num_players)
    ])


@patch("randovania.layout.generator_parameters.GeneratorParameters.bit_pack_encode", autospec=True)
def test_as_bytes_caches(mock_bit_pack_encode: MagicMock,
                         default_echoes_preset):
    # Setup
    mock_bit_pack_encode.return_value = [
        (5, 256)
    ]
    params = GeneratorParameters(
        seed_number=1000,
        spoiler=True,
        presets=[default_echoes_preset],
    )

    # Run
    str1 = params.as_bytes
    str2 = params.as_bytes

    # Assert
    assert str1 == b'\x05'
    assert str1 == str2
    assert object.__getattribute__(params, "__cached_as_bytes") is not None
    mock_bit_pack_encode.assert_called_once_with(params, {})


def test_development_rng(default_blank_preset):
    params = GeneratorParameters(
        seed_number=1000,
        spoiler=True,
        development=True,
        presets=[default_blank_preset],
    )

    # Run
    rng = params.create_rng()

    # Assert
    assert rng.randint(100, 900) == 896
