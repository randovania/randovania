from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from randovania.games.game import RandovaniaGame
from randovania.games.prime2.exporter import patch_data_factory
from randovania.games.prime2.layout.echoes_cosmetic_patches import EchoesCosmeticPatches
from randovania.games.prime2.layout.echoes_cosmetic_suits import EchoesSuitPreferences, SuitColor
from randovania.layout.lib.teleporters import TeleporterList, TeleporterShuffleMode

if TYPE_CHECKING:
    import pytest_mock


def test_should_keep_elevator_sounds_vanilla(default_echoes_configuration):
    assert patch_data_factory.should_keep_elevator_sounds(default_echoes_configuration)


def test_should_keep_elevator_sounds_one_way_anywhere(default_echoes_configuration):
    config = dataclasses.replace(
        default_echoes_configuration,
        teleporters=dataclasses.replace(
            default_echoes_configuration.teleporters, mode=TeleporterShuffleMode.ONE_WAY_ANYTHING
        ),
    )
    assert not patch_data_factory.should_keep_elevator_sounds(config)


def test_should_keep_elevator_two_way(default_echoes_configuration):
    config = dataclasses.replace(
        default_echoes_configuration,
        teleporters=dataclasses.replace(
            default_echoes_configuration.teleporters, mode=TeleporterShuffleMode.TWO_WAY_UNCHECKED
        ),
    )
    assert patch_data_factory.should_keep_elevator_sounds(config)


def test_should_keep_elevator_with_stg(default_echoes_configuration):
    config = dataclasses.replace(
        default_echoes_configuration,
        teleporters=dataclasses.replace(
            default_echoes_configuration.teleporters,
            mode=TeleporterShuffleMode.TWO_WAY_UNCHECKED,
            excluded_teleporters=TeleporterList.with_elements([], RandovaniaGame.METROID_PRIME_ECHOES),
        ),
    )
    assert not patch_data_factory.should_keep_elevator_sounds(config)


@pytest.mark.parametrize(
    ("randomize_separately", "expected"),
    [
        (None, {"varia": "player2", "dark": "player3", "light": "player4"}),
        (False, {"varia": "player1", "dark": "player1", "light": "player1"}),
        (True, {"varia": "player1", "dark": "player2", "light": "player3"}),
    ],
)
def test_suit_cosmetics(randomize_separately: bool | None, expected: dict, mocker: pytest_mock.MockerFixture):
    # Setup test cases
    if randomize_separately is None:
        suits = EchoesSuitPreferences(
            varia=SuitColor.PLAYER_2,
            dark=SuitColor.PLAYER_3,
            light=SuitColor.PLAYER_4,
        )
        choice_expected = 0
    else:
        suits = EchoesSuitPreferences(
            varia=SuitColor.RANDOM,
            dark=SuitColor.RANDOM,
            light=SuitColor.RANDOM,
            randomize_separately=randomize_separately,
        )
        choice_expected = 3 if randomize_separately else 1
    cosmetics = EchoesCosmeticPatches(suit_colors=suits)

    # Mocks
    description = MagicMock()
    description.get_seed_for_player = lambda _: 0

    players = MagicMock()

    choices = (suit for suit in SuitColor)

    def choice(*args):
        return next(choices)

    mock_choice = mocker.patch("random.Random.choice", side_effect=choice)

    mocker.patch("randovania.layout.filtered_database.game_description_for_layout")
    mocker.patch("randovania.games.prime2.exporter.hint_namer.EchoesHintNamer")

    # Run
    factory = patch_data_factory.EchoesPatchDataFactory(description, players, cosmetics)

    result = factory.add_new_patcher_cosmetics()["suits"]

    # Assert
    assert mock_choice.call_count == choice_expected
    assert result == expected
