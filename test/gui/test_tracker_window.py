from __future__ import annotations

import copy
import dataclasses
import json
from typing import TYPE_CHECKING

import pytest

from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.games.prime2.layout.translator_configuration import LayoutTranslatorRequirement
from randovania.gui import tracker_window
from randovania.layout.lib.teleporters import TeleporterShuffleMode
from randovania.layout.versioned_preset import VersionedPreset

if TYPE_CHECKING:
    from pathlib import Path
    from unittest.mock import MagicMock


@pytest.fixture(params=[{}, {"teleporters": TeleporterShuffleMode.ONE_WAY_ANYTHING, "translator_configuration": True}])
def layout_config(request, default_echoes_configuration):
    if "translator_configuration" in request.param:
        translator_requirement = copy.copy(default_echoes_configuration.translator_configuration.translator_requirement)
        for gate in translator_requirement.keys():
            translator_requirement[gate] = LayoutTranslatorRequirement.RANDOM
            break

        new_gate = dataclasses.replace(
            default_echoes_configuration.translator_configuration, translator_requirement=translator_requirement
        )
        request.param["translator_configuration"] = new_gate
    return dataclasses.replace(default_echoes_configuration, **request.param)


def test_load_previous_state_no_previous_layout(tmp_path: Path, default_echoes_configuration):
    # Run
    result = tracker_window._load_previous_state(tmp_path, default_echoes_configuration)

    # Assert
    assert result is None


def test_load_previous_state_previous_layout_not_json(tmp_path: Path, default_echoes_configuration):
    # Setup
    tmp_path.joinpath("preset.rdvpreset").write_text("this is not a json")

    # Run
    result = tracker_window._load_previous_state(tmp_path, default_echoes_configuration)

    # Assert
    assert result is None


def test_load_previous_state_previous_layout_not_layout(tmp_path: Path, default_echoes_configuration):
    # Setup
    tmp_path.joinpath("preset.rdvpreset").write_text(json.dumps({"trick_level": "foo"}))
    tmp_path.joinpath("state.json").write_text("[]")

    # Run
    result = tracker_window._load_previous_state(tmp_path, default_echoes_configuration)

    # Assert
    assert result is None


def test_load_previous_state_missing_state(tmp_path: Path, default_preset):
    # Setup
    VersionedPreset.with_preset(default_preset).save_to_file(tmp_path.joinpath("preset.rdvpreset"))

    # Run
    result = tracker_window._load_previous_state(tmp_path, default_preset.configuration)

    # Assert
    assert result is None


def test_load_previous_state_invalid_state(tmp_path: Path, default_preset):
    # Setup
    VersionedPreset.with_preset(default_preset).save_to_file(tmp_path.joinpath("preset.rdvpreset"))
    tmp_path.joinpath("state.json").write_text("")

    # Run
    result = tracker_window._load_previous_state(tmp_path, default_preset.configuration)

    # Assert
    assert result is None


def test_load_previous_state_success(tmp_path: Path, default_preset):
    # Setup
    data = {"asdf": 5, "zxcv": 123}
    VersionedPreset.with_preset(default_preset).save_to_file(tmp_path.joinpath("preset.rdvpreset"))
    tmp_path.joinpath("state.json").write_text(json.dumps(data))

    # Run
    result = tracker_window._load_previous_state(tmp_path, default_preset.configuration)

    # Assert
    assert result == data


@pytest.mark.parametrize("shuffle_advanced", [False, True])
async def test_apply_previous_state(
    skip_qtbot, tmp_path: Path, default_echoes_preset, shuffle_advanced, echoes_game_description
):
    configuration = default_echoes_preset.configuration
    assert isinstance(configuration, EchoesConfiguration)

    if shuffle_advanced:
        translator_requirement = copy.copy(configuration.translator_configuration.translator_requirement)
        for gate in translator_requirement.keys():
            translator_requirement[gate] = LayoutTranslatorRequirement.RANDOM
            break

        new_gate = dataclasses.replace(
            configuration.translator_configuration, translator_requirement=translator_requirement
        )
        layout_config = dataclasses.replace(
            configuration,
            teleporters=dataclasses.replace(
                configuration.teleporters,
                mode=TeleporterShuffleMode.ONE_WAY_ANYTHING,
            ),
            translator_configuration=new_gate,
        )

        preset = dataclasses.replace(default_echoes_preset.fork(), configuration=layout_config)

    else:
        preset = default_echoes_preset

    state: dict = {
        "actions": ["Temple Grounds/Landing Site/Save Station"],
        "collected_pickups": {
            "Amber Translator": 0,
            "Annihilator Beam": 0,
            "Boost Ball": 0,
            "Cobalt Translator": 0,
            "Dark Agon Key 1": 0,
            "Dark Agon Key 2": 0,
            "Dark Agon Key 3": 0,
            "Dark Ammo Expansion": 0,
            "Dark Beam": 0,
            "Dark Torvus Key 1": 0,
            "Dark Torvus Key 2": 0,
            "Dark Torvus Key 3": 0,
            "Dark Visor": 0,
            "Darkburst": 0,
            "Echo Visor": 0,
            "Emerald Translator": 0,
            "Energy Tank": 0,
            "Grapple Beam": 0,
            "Gravity Boost": 0,
            "Ing Hive Key 1": 0,
            "Ing Hive Key 2": 0,
            "Ing Hive Key 3": 0,
            "Light Ammo Expansion": 0,
            "Light Beam": 0,
            "Missile Expansion": 0,
            "Missile Launcher": 0,
            "Morph Ball Bomb": 0,
            "Power Bomb": 0,
            "Power Bomb Expansion": 0,
            "Progressive Suit": 0,
            "Screw Attack": 0,
            "Seeker Launcher": 0,
            "Sky Temple Key 1": 0,
            "Sky Temple Key 2": 0,
            "Sky Temple Key 3": 0,
            "Sky Temple Key 4": 0,
            "Sky Temple Key 5": 0,
            "Sky Temple Key 6": 0,
            "Sky Temple Key 7": 0,
            "Sky Temple Key 8": 0,
            "Sky Temple Key 9": 0,
            "Sonic Boom": 0,
            "Space Jump Boots": 1,
            "Spider Ball": 0,
            "Sunburst": 0,
            "Super Missile": 0,
            "Violet Translator": 0,
        },
        "teleporters": [
            {
                "data": None,
                "teleporter": {
                    "area": "Transport to Temple Grounds",
                    "node": "Elevator to Temple Grounds",
                    "region": "Agon Wastes",
                },
            },
            {
                "data": None,
                "teleporter": {
                    "area": "Transport to Torvus Bog",
                    "node": "Elevator to Torvus Bog",
                    "region": "Agon Wastes",
                },
            },
            {
                "data": None,
                "teleporter": {
                    "area": "Transport to Sanctuary Fortress",
                    "node": "Elevator to Sanctuary Fortress",
                    "region": "Agon Wastes",
                },
            },
            {
                "data": None,
                "teleporter": {
                    "area": "Temple Transport C",
                    "node": "Elevator to Temple Grounds",
                    "region": "Great Temple",
                },
            },
            {
                "data": None,
                "teleporter": {
                    "area": "Temple Transport A",
                    "node": "Elevator to Temple Grounds",
                    "region": "Great Temple",
                },
            },
            {
                "data": None,
                "teleporter": {
                    "area": "Temple Transport B",
                    "node": "Elevator to Temple Grounds",
                    "region": "Great Temple",
                },
            },
            {
                "data": None,
                "teleporter": {
                    "area": "Aerie",
                    "node": "Elevator to Aerie Transport Station",
                    "region": "Sanctuary Fortress",
                },
            },
            {
                "data": None,
                "teleporter": {
                    "area": "Aerie Transport Station",
                    "node": "Elevator to Aerie",
                    "region": "Sanctuary Fortress",
                },
            },
            {
                "data": None,
                "teleporter": {
                    "area": "Transport to Temple Grounds",
                    "node": "Elevator to Temple Grounds",
                    "region": "Sanctuary Fortress",
                },
            },
            {
                "data": None,
                "teleporter": {
                    "area": "Transport to Agon Wastes",
                    "node": "Elevator to Agon Wastes",
                    "region": "Sanctuary Fortress",
                },
            },
            {
                "data": None,
                "teleporter": {
                    "area": "Transport to Torvus Bog",
                    "node": "Elevator to Torvus Bog",
                    "region": "Sanctuary Fortress",
                },
            },
            {
                "data": None,
                "teleporter": {
                    "area": "Sky Temple Energy Controller",
                    "node": "Elevator to Temple Grounds",
                    "region": "Great Temple",
                },
            },
            {
                "data": None,
                "teleporter": {
                    "area": "Sky Temple Gateway",
                    "node": "Elevator to Great Temple",
                    "region": "Temple Grounds",
                },
            },
            {
                "data": None,
                "teleporter": {
                    "area": "Transport to Agon Wastes",
                    "node": "Elevator to Agon Wastes",
                    "region": "Temple Grounds",
                },
            },
            {
                "data": None,
                "teleporter": {
                    "area": "Temple Transport B",
                    "node": "Elevator to Great Temple",
                    "region": "Temple Grounds",
                },
            },
            {
                "data": None,
                "teleporter": {
                    "area": "Transport to Sanctuary Fortress",
                    "node": "Elevator to Sanctuary Fortress",
                    "region": "Temple Grounds",
                },
            },
            {
                "data": None,
                "teleporter": {
                    "area": "Temple Transport A",
                    "node": "Elevator to Great Temple",
                    "region": "Temple Grounds",
                },
            },
            {
                "data": None,
                "teleporter": {
                    "area": "Transport to Torvus Bog",
                    "node": "Elevator to Torvus Bog",
                    "region": "Temple Grounds",
                },
            },
            {
                "data": None,
                "teleporter": {
                    "area": "Temple Transport C",
                    "node": "Elevator to Great Temple",
                    "region": "Temple Grounds",
                },
            },
            {
                "data": None,
                "teleporter": {
                    "area": "Transport to Sanctuary Fortress",
                    "node": "Elevator to Sanctuary Fortress",
                    "region": "Torvus Bog",
                },
            },
            {
                "data": None,
                "teleporter": {
                    "area": "Transport to Temple Grounds",
                    "node": "Elevator to Temple Grounds",
                    "region": "Torvus Bog",
                },
            },
            {
                "data": None,
                "teleporter": {
                    "area": "Transport to Agon Wastes",
                    "node": "Elevator to Agon Wastes",
                    "region": "Torvus Bog",
                },
            },
        ],
        "configurable_nodes": {
            "Agon Wastes/Mining Plaza/Translator Gate": None,
            "Agon Wastes/Mining Station A/Translator Gate": None,
            "Great Temple/Temple Sanctuary/Transport A Translator Gate": None,
            "Great Temple/Temple Sanctuary/Transport B Translator Gate": None,
            "Great Temple/Temple Sanctuary/Transport C Translator Gate": None,
            "Sanctuary Fortress/Reactor Core/Translator Gate": None,
            "Sanctuary Fortress/Sanctuary Temple/Translator Gate": None,
            "Temple Grounds/GFMC Compound/Translator Gate": None,
            "Temple Grounds/Hive Access Tunnel/Translator Gate": None,
            "Temple Grounds/Hive Transport Area/Translator Gate": None,
            "Temple Grounds/Industrial Site/Translator Gate": None,
            "Temple Grounds/Meeting Grounds/Translator Gate": None,
            "Temple Grounds/Path of Eyes/Translator Gate": None,
            "Temple Grounds/Temple Assembly Site/Translator Gate": None,
            "Torvus Bog/Great Bridge/Translator Gate": None,
            "Torvus Bog/Torvus Temple/Elevator Translator Scan": None,
            "Torvus Bog/Torvus Temple/Translator Gate": None,
        },
        "starting_location": {"region": "Temple Grounds", "area": "Landing Site", "node": "Save Station"},
    }

    if shuffle_advanced:
        for teleporter in state["teleporters"]:
            if (
                teleporter["teleporter"]["region"] == "Agon Wastes"
                and teleporter["teleporter"]["node"] == "Elevator to Sanctuary Fortress"
                and teleporter["teleporter"]["area"] == "Transport to Sanctuary Fortress"
            ):
                teleporter["data"] = {
                    "area": "Agon Energy Controller",
                    "region": "Agon Wastes",
                    "node": "Door to Controller Access",
                }
        state["configurable_nodes"]["Temple Grounds/Hive Access Tunnel/Translator Gate"] = "violet"
    VersionedPreset.with_preset(preset).save_to_file(tmp_path.joinpath("preset.rdvpreset"))
    tmp_path.joinpath("state.json").write_text(json.dumps(state), "utf-8")

    # Run
    window = await tracker_window.TrackerWindow.create_new(tmp_path, preset)
    skip_qtbot.add_widget(window)

    # Assert
    assert window.state_for_current_configuration() is not None
    persisted_data = json.loads(tmp_path.joinpath("state.json").read_text("utf-8"))
    assert persisted_data == state

    window.reset()
    window.persist_current_state()

    persisted_data = json.loads(tmp_path.joinpath("state.json").read_text("utf-8"))
    assert persisted_data != state


async def test_load_multi_starting_location(
    skip_qtbot, tmp_path: Path, default_echoes_configuration, default_echoes_preset, mocker
):
    new_start_loc = (
        NodeIdentifier.create("Temple Grounds", "Landing Site", "Save Station"),
        NodeIdentifier.create("Temple Grounds", "Temple Transport C", "Elevator to Great Temple"),
    )
    layout_config = dataclasses.replace(
        default_echoes_configuration,
        starting_location=dataclasses.replace(default_echoes_configuration.starting_location, locations=new_start_loc),
    )
    preset = dataclasses.replace(default_echoes_preset.fork(), configuration=layout_config)
    mock_return = ("Temple Grounds/Temple Transport C/Elevator to Great Temple", True)

    # Run
    mock_get_item: MagicMock = mocker.patch("PySide6.QtWidgets.QInputDialog.getItem", return_value=mock_return)
    window = await tracker_window.TrackerWindow.create_new(tmp_path, preset)
    skip_qtbot.add_widget(window)

    # Assert
    mock_get_item.assert_called_once()
    state = window.state_for_current_configuration()
    assert state is not None
    assert state.node.identifier == new_start_loc[1]


async def test_load_single_starting_location(
    skip_qtbot, tmp_path: Path, default_echoes_configuration, default_echoes_preset
):
    new_start_loc = (NodeIdentifier.create("Temple Grounds", "Temple Transport C", "Elevator to Great Temple"),)
    layout_config = dataclasses.replace(
        default_echoes_configuration,
        starting_location=dataclasses.replace(default_echoes_configuration.starting_location, locations=new_start_loc),
    )
    preset = dataclasses.replace(default_echoes_preset.fork(), configuration=layout_config)

    # Run
    window = await tracker_window.TrackerWindow.create_new(tmp_path, preset)
    skip_qtbot.add_widget(window)

    # Assert
    state = window.state_for_current_configuration()
    assert state is not None
    assert state.node.identifier == new_start_loc[0]


async def test_preset_without_starting_location(
    skip_qtbot, tmp_path: Path, default_echoes_configuration, default_echoes_preset
):
    new_start_loc = ()
    layout_config = dataclasses.replace(
        default_echoes_configuration,
        starting_location=dataclasses.replace(default_echoes_configuration.starting_location, locations=new_start_loc),
    )
    preset = dataclasses.replace(default_echoes_preset.fork(), configuration=layout_config)

    # Run
    with pytest.raises(ValueError, match="Preset without a starting location"):
        await tracker_window.TrackerWindow.create_new(tmp_path, preset)
