import dataclasses

from randovania.games.game import RandovaniaGame
from randovania.games.prime2.exporter import patch_data_factory
from randovania.layout.lib.teleporters import TeleporterShuffleMode, TeleporterList


def test_should_keep_elevator_sounds_vanilla(default_echoes_configuration):
    assert patch_data_factory.should_keep_elevator_sounds(default_echoes_configuration)


def test_should_keep_elevator_sounds_one_way_anywhere(default_echoes_configuration):
    config = dataclasses.replace(
        default_echoes_configuration,
        elevators=dataclasses.replace(default_echoes_configuration.elevators,
                                      mode=TeleporterShuffleMode.ONE_WAY_ANYTHING)
    )
    assert not patch_data_factory.should_keep_elevator_sounds(config)


def test_should_keep_elevator_two_way(default_echoes_configuration):
    config = dataclasses.replace(
        default_echoes_configuration,
        elevators=dataclasses.replace(default_echoes_configuration.elevators,
                                      mode=TeleporterShuffleMode.TWO_WAY_UNCHECKED)
    )
    assert patch_data_factory.should_keep_elevator_sounds(config)


def test_should_keep_elevator_with_stg(default_echoes_configuration):
    config = dataclasses.replace(
        default_echoes_configuration,
        elevators=dataclasses.replace(
            default_echoes_configuration.elevators,
            mode=TeleporterShuffleMode.TWO_WAY_UNCHECKED,
            excluded_teleporters=TeleporterList.with_elements([], RandovaniaGame.METROID_PRIME_ECHOES),
        )
    )
    assert not patch_data_factory.should_keep_elevator_sounds(config)
