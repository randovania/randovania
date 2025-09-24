import dataclasses

import pytest

from randovania.game.game_enum import RandovaniaGame
from randovania.layout.lib.teleporters import TeleporterShuffleMode
from randovania.lib import enum_lib


@pytest.mark.parametrize(
    "shuffle_mode",
    list(enum_lib.iterate_enum(TeleporterShuffleMode)),
)
@pytest.mark.parametrize(
    "final_bosses",
    [True, False],
)
def test_prime_static_assignments(preset_manager, shuffle_mode, final_bosses):
    # Setup
    base = preset_manager.default_preset_for_game(RandovaniaGame.METROID_PRIME).get_preset()

    base = dataclasses.replace(
        base,
        configuration=dataclasses.replace(
            base.configuration,
            teleporters=dataclasses.replace(
                base.configuration.teleporters, skip_final_bosses=final_bosses, mode=shuffle_mode
            ),
        ),
    )

    # Run
    static_assignments = base.configuration.teleporters.static_teleporters

    # Assert

    try:
        source, target = next(iter(static_assignments.items()))
    except StopIteration:
        source, target = None, None

    if final_bosses:
        assert len(static_assignments) == 1
        assert source.area == "Artifact Temple"
        assert target.area == "Credits"
    elif not final_bosses and shuffle_mode in [
        TeleporterShuffleMode.ONE_WAY_TELEPORTER,
        TeleporterShuffleMode.ONE_WAY_TELEPORTER_REPLACEMENT,
    ]:
        assert len(static_assignments) == 1
        assert source.area == "Metroid Prime Lair"
        assert target.area == "Credits"
    else:
        assert len(static_assignments) == 0


@pytest.mark.parametrize(
    "shuffle_mode",
    list(enum_lib.iterate_enum(TeleporterShuffleMode)),
)
@pytest.mark.parametrize(
    "final_bosses",
    [True, False],
)
def test_echoes_static_assignments(preset_manager, shuffle_mode, final_bosses):
    # Setup
    base = preset_manager.default_preset_for_game(RandovaniaGame.METROID_PRIME_ECHOES).get_preset()

    base = dataclasses.replace(
        base,
        configuration=dataclasses.replace(
            base.configuration,
            teleporters=dataclasses.replace(
                base.configuration.teleporters, skip_final_bosses=final_bosses, mode=shuffle_mode
            ),
        ),
    )

    # Run
    static_assignments = base.configuration.teleporters.static_teleporters

    # Assert

    try:
        source, target = next(iter(static_assignments.items()))
    except StopIteration:
        source, target = None, None

    if final_bosses:
        assert len(static_assignments) == 1
        assert source.area == "Sky Temple Gateway"
        assert target.area == "Credits"
    else:
        assert len(static_assignments) == 0
