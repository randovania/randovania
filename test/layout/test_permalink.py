from __future__ import annotations

import contextlib
import re
from unittest.mock import MagicMock

import pytest

from randovania.bitpacking import bitpacking
from randovania.games.game import RandovaniaGame
from randovania.layout import generator_parameters
from randovania.layout.generator_parameters import GeneratorParameters
from randovania.layout.permalink import Permalink, UnsupportedPermalink


@pytest.fixture()
def fake_generator_parameters() -> GeneratorParameters:
    parameters = MagicMock(spec=GeneratorParameters)
    parameters.as_bytes = b"\xa0\xb0\xc0"
    return parameters


def test_encode(fake_generator_parameters):
    # Setup
    link = Permalink(parameters=fake_generator_parameters, seed_hash=None, randovania_version=b"0123")

    # Run
    encoded = link.as_base64_str

    # Assert
    assert encoded == "DX4wMTIzAx6sOvRw"


@pytest.mark.parametrize("invalid", [False, True])
def test_decode(mocker, invalid):
    games = (RandovaniaGame.METROID_PRIME_ECHOES, RandovaniaGame.METROID_DREAD)
    mock_from_bytes: MagicMock = mocker.patch(
        "randovania.layout.generator_parameters.GeneratorParameters.from_bytes", autospec=True
    )
    parameters = mock_from_bytes.return_value
    parameters.as_bytes = bitpacking.pack_results_and_bit_count(generator_parameters.encode_game_list(games))[0]
    if invalid:
        mock_from_bytes.side_effect = ValueError("Invalid Permalink")

    # This test should break whenever we change how permalinks are created
    # When this happens, we must bump the permalink version and change the tests
    encoded = "DSkwMTIzAm3yAINX"

    expected = Permalink(
        parameters=parameters,
        seed_hash=None,
        randovania_version=b"0123",
    )

    # Uncomment this line to quickly get the new encoded permalink
    # assert expected.as_base64_str == ""
    # print(expected.as_base64_str)

    if invalid:
        expectation = pytest.raises(UnsupportedPermalink)
    else:
        expectation = contextlib.nullcontext()

    # Run
    with expectation as exp:
        link = Permalink.from_str(encoded)

    # Assert
    mock_from_bytes.assert_called_once_with(b"D\xa0")
    if invalid:
        assert exp.value.games == games
    else:
        assert link == expected


@pytest.mark.parametrize(
    ("invalid", "err"),
    [
        ("", "String too short"),
        ("a", r"Invalid base64-encoded string: number of data characters \(1\) cannot be 1 more than a multiple of 4"),
        ("x", r"Invalid base64-encoded string: number of data characters \(1\) cannot be 1 more than a multiple of 4"),
        ("zz", "String too short"),
        (
            "AAAAfRxALWmCI50gIQD",
            r"Given permalink has version 0, but this Randovania support only permalink of version \d+.",
        ),
        (
            "AAAAfRxALxmCI50gIQDy",
            r"Given permalink has version 0, but this Randovania support only permalink of version \d+.",
        ),
    ],
)
def test_decode_invalid(invalid: str, err: str):
    with pytest.raises(ValueError, match=err):
        Permalink.from_str(invalid)


@pytest.mark.parametrize(
    "seed_hash",
    [
        None,
        b"12345",
        b"67890",
    ],
)
def test_round_trip(seed_hash, fake_generator_parameters, mocker):
    mock_from_bytes: MagicMock = mocker.patch(
        "randovania.layout.generator_parameters.GeneratorParameters.from_bytes",
        autospec=True,
        return_value=fake_generator_parameters,
    )
    # Setup
    link = Permalink(parameters=fake_generator_parameters, seed_hash=seed_hash, randovania_version=b"0123")

    # Run
    after = Permalink.from_str(link.as_base64_str)

    # Assert
    assert link == after
    mock_from_bytes.assert_called_once_with(b"\xa0\xb0\xc0")


@pytest.mark.parametrize(
    ("permalink", "version"),
    [
        ("CrhkAGTOLJD7Kf6Y", 10),
        ("DLhkAGTOLJD7Kf6Y", 12),
    ],
)
def test_decode_old_version(permalink: str, version: int):
    expect = (
        f"Given permalink has version {version}, "
        f"but this Randovania support only permalink of version {Permalink.current_schema_version()}."
    )
    with pytest.raises(ValueError, match=re.escape(expect)):
        Permalink.from_str(permalink)
