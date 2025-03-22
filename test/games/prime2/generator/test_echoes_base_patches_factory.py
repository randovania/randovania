from __future__ import annotations

import dataclasses
import random
from unittest.mock import MagicMock

from randovania.games.prime2.generator.base_patches_factory import EchoesBasePatchesFactory
from randovania.games.prime2.generator.teleporter_distributor import elevator_echoes_shuffled
from randovania.games.prime2.layout.translator_configuration import LayoutTranslatorRequirement


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
    result = factory.assign_static_dock_weakness(
        default_echoes_configuration, echoes_game_description, echoes_game_patches
    )

    # Result
    assert list(result.all_dock_weaknesses()) == []


def test_save_stations_unlocked(echoes_game_patches, default_echoes_configuration, echoes_game_description):
    factory = EchoesBasePatchesFactory()
    config = dataclasses.replace(default_echoes_configuration, blue_save_doors=True)

    # Run
    result = factory.assign_static_dock_weakness(config, echoes_game_description, echoes_game_patches)

    # Result
    assert len(list(result.all_dock_weaknesses())) == 18 * 2


def test_gate_assignment_for_configuration_all_emerald(echoes_game_description, default_echoes_configuration):
    # Setup
    factory = EchoesBasePatchesFactory()

    translator_configuration = default_echoes_configuration.translator_configuration
    configuration = dataclasses.replace(
        default_echoes_configuration,
        translator_configuration=dataclasses.replace(
            translator_configuration,
            translator_requirement=dict.fromkeys(
                translator_configuration.translator_requirement.keys(), LayoutTranslatorRequirement.EMERALD
            ),
        ),
    )

    rng = MagicMock()

    # Run
    results = factory.create_game_specific(configuration, echoes_game_description, rng)

    # Assert
    assert list(results.keys()) == ["translator_gates"]
    associated_requirements = list(results["translator_gates"].values())
    assert associated_requirements == [LayoutTranslatorRequirement.EMERALD.value] * len(
        translator_configuration.translator_requirement
    )


def test_gate_assignment_for_configuration_all_random(echoes_game_description, default_echoes_configuration):
    # Setup
    factory = EchoesBasePatchesFactory()

    translator_configuration = default_echoes_configuration.translator_configuration
    configuration = dataclasses.replace(
        default_echoes_configuration,
        translator_configuration=translator_configuration.with_full_random(),
    )

    requirements = [
        LayoutTranslatorRequirement.EMERALD.value,
        LayoutTranslatorRequirement.VIOLET.value,
    ]
    requirements = requirements * len(translator_configuration.translator_requirement)

    choices = [LayoutTranslatorRequirement.EMERALD, LayoutTranslatorRequirement.VIOLET]
    rng = MagicMock()
    rng.choice.side_effect = choices * len(translator_configuration.translator_requirement)

    # Run
    results = factory.create_game_specific(configuration, echoes_game_description, rng)

    # Assert
    assert list(results.keys()) == ["translator_gates"]
    associated_requirements = list(results["translator_gates"].values())
    assert associated_requirements == requirements[: len(translator_configuration.translator_requirement)]
