from __future__ import annotations

import dataclasses
import random

from randovania.games.prime2.generator.base_patches_factory import EchoesBasePatchesFactory
from randovania.games.prime2.generator.teleporter_distributor import elevator_echoes_shuffled


def test_elevator_echoes_shuffled(echoes_game_patches):
    EchoesBasePatchesFactory()
    rng = random.Random(1000)

    # Run
    result = elevator_echoes_shuffled(echoes_game_patches.game, rng)

    # Assert
    gt = "Great Temple"
    tg = "Temple Grounds"
    sf = "Sanctuary Fortress"
    aw = "Agon Wastes"

    simpler = {source.as_string: target.as_string for source, target in result.items()}
    assert simpler == {
        f"{aw}/Transport to {sf}/Elevator to {sf}": f"{tg}/Temple Transport B/Elevator to {gt}",
        f"{aw}/Transport to {tg}/Elevator to {tg}": f"{tg}/Temple Transport A/Elevator to {gt}",
        f"{aw}/Transport to Torvus Bog/Elevator to Torvus Bog": f"{tg}/Temple Transport C/Elevator to {gt}",
        f"{gt}/Temple Transport A/Elevator to {tg}": f"{tg}/Transport to {aw}/Elevator to {aw}",
        f"{gt}/Temple Transport B/Elevator to {tg}": f"{sf}/Transport to {aw}/Elevator to {aw}",
        f"{gt}/Temple Transport C/Elevator to {tg}": f"Torvus Bog/Transport to {aw}/Elevator to {aw}",
        f"{sf}/Transport to {aw}/Elevator to {aw}": f"{gt}/Temple Transport B/Elevator to {tg}",
        f"{sf}/Transport to {tg}/Elevator to {tg}": f"{tg}/Transport to {sf}/Elevator to {sf}",
        f"{sf}/Transport to Torvus Bog/Elevator to Torvus Bog": f"Torvus Bog/Transport to {sf}/Elevator to {sf}",
        f"{tg}/Temple Transport A/Elevator to {gt}": f"{aw}/Transport to {tg}/Elevator to {tg}",
        f"{tg}/Temple Transport B/Elevator to {gt}": f"{aw}/Transport to {sf}/Elevator to {sf}",
        f"{tg}/Temple Transport C/Elevator to {gt}": f"{aw}/Transport to Torvus Bog/Elevator to Torvus Bog",
        f"{tg}/Transport to {aw}/Elevator to {aw}": f"{gt}/Temple Transport A/Elevator to {tg}",
        f"{tg}/Transport to {sf}/Elevator to {sf}": f"{sf}/Transport to {tg}/Elevator to {tg}",
        f"{tg}/Transport to Torvus Bog/Elevator to Torvus Bog": f"Torvus Bog/Transport to {tg}/Elevator to {tg}",
        f"Torvus Bog/Transport to {aw}/Elevator to {aw}": f"{gt}/Temple Transport C/Elevator to {tg}",
        f"Torvus Bog/Transport to {sf}/Elevator to {sf}": f"{sf}/Transport to Torvus Bog/Elevator to Torvus Bog",
        f"Torvus Bog/Transport to {tg}/Elevator to {tg}": f"{tg}/Transport to Torvus Bog/Elevator to Torvus Bog",
    }


def test_save_stations_not_unlocked(echoes_game_patches, default_echoes_configuration, echoes_game_description):
    factory = EchoesBasePatchesFactory()

    # Run
    result = factory.assign_save_door_weaknesses(
        echoes_game_patches, default_echoes_configuration, echoes_game_description
    )

    # Result
    assert list(result.all_dock_weaknesses()) == []


def test_save_stations_unlocked(echoes_game_patches, default_echoes_configuration, echoes_game_description):
    factory = EchoesBasePatchesFactory()
    config = dataclasses.replace(default_echoes_configuration, blue_save_doors=True)

    # Run
    result = factory.assign_save_door_weaknesses(echoes_game_patches, config, echoes_game_description)

    # Result
    assert len(list(result.all_dock_weaknesses())) == 18 * 2
