from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from randovania.games.common.prime_family.gui import export_validator


def test_discover_game_missing(tmp_path):
    assert export_validator.discover_game(tmp_path.joinpath("missing.py")) is None


def test_discover_good_iso(mocker):
    disc, is_wii = MagicMock(), MagicMock()
    mock_open_disc: MagicMock = mocker.patch("nod.open_disc_from_image", return_value=(disc, is_wii))
    header = disc.get_data_partition.return_value.get_header.return_value
    header.game_id = b"GameId"
    header.game_title = b"The Game Title\x00\x00\x00"
    the_path = MagicMock()

    # Run
    result = export_validator.discover_game(the_path)

    # Assert
    assert result == ("GameId", "The Game Title")
    mock_open_disc.assert_called_once_with(the_path)


def test_discover_bad_iso(mocker):
    mock_open_disc: MagicMock = mocker.patch("nod.open_disc_from_image", side_effect=RuntimeError("bad iso"))
    the_path = MagicMock()

    # Run
    result = export_validator.discover_game(the_path)

    # Assert
    assert result is None
    mock_open_disc.assert_called_once_with(the_path)


def test_is_prime1_iso_validator_not_iso(mocker, tmp_path):
    the_path = tmp_path.joinpath("input.ciso")
    the_path.write_bytes(b"foo")
    mock_discover_game: MagicMock = mocker.patch(
        "randovania.games.common.prime_family.gui.export_validator.discover_game"
    )

    # Run
    result = export_validator.is_prime1_iso_validator(the_path)

    # Assert
    mock_discover_game.assert_not_called()
    assert not result


@pytest.mark.parametrize("good_iso", [False, True])
def test_is_prime1_iso_validator_iso(mocker, tmp_path, good_iso):
    the_path = tmp_path.joinpath("input.iso")
    the_path.write_bytes(b"foo")
    mock_discover_game: MagicMock = mocker.patch(
        "randovania.games.common.prime_family.gui.export_validator.discover_game",
        return_value=("GM8E01", "Metroid Prime") if good_iso else None,
    )

    # Run
    result = export_validator.is_prime1_iso_validator(the_path)

    # Assert
    mock_discover_game.assert_called_once_with(the_path)
    assert result != good_iso


@pytest.mark.parametrize("good_iso", [False, True])
def test_is_prime2_iso_validator_iso(mocker, tmp_path, good_iso):
    the_path = tmp_path.joinpath("input.iso")
    the_path.write_bytes(b"foo")
    mock_discover_game: MagicMock = mocker.patch(
        "randovania.games.common.prime_family.gui.export_validator.discover_game",
        return_value=("G2ME01", "Metroid Prime 2") if good_iso else None,
    )

    # Run
    result = export_validator.is_prime2_iso_validator(the_path)

    # Assert
    mock_discover_game.assert_called_once_with(the_path)
    assert result != good_iso
