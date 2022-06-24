import copy
import dataclasses
import json
from pathlib import Path

import pytest

from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.games.prime2.layout.translator_configuration import LayoutTranslatorRequirement
from randovania.gui import tracker_window
from randovania.layout.lib.teleporters import TeleporterShuffleMode
from randovania.layout.versioned_preset import VersionedPreset


@pytest.fixture(params=[{},
                        {"elevators": TeleporterShuffleMode.ONE_WAY_ANYTHING,
                         "translator_configuration": True}],
                name="layout_config")
def _layout_config(request, default_echoes_configuration):
    if "translator_configuration" in request.param:
        translator_requirement = copy.copy(default_echoes_configuration.translator_configuration.translator_requirement)
        for gate in translator_requirement.keys():
            translator_requirement[gate] = LayoutTranslatorRequirement.RANDOM
            break

        new_gate = dataclasses.replace(default_echoes_configuration.translator_configuration,
                                       translator_requirement=translator_requirement)
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
async def test_apply_previous_state(skip_qtbot, tmp_path: Path, default_echoes_preset, shuffle_advanced,
                                    echoes_game_description):
    configuration = default_echoes_preset.configuration
    assert isinstance(configuration, EchoesConfiguration)

    if shuffle_advanced:
        translator_requirement = copy.copy(
            configuration.translator_configuration.translator_requirement)
        for gate in translator_requirement.keys():
            translator_requirement[gate] = LayoutTranslatorRequirement.RANDOM
            break

        new_gate = dataclasses.replace(configuration.translator_configuration,
                                       translator_requirement=translator_requirement)
        layout_config = dataclasses.replace(
            configuration,
            elevators=dataclasses.replace(
                configuration.elevators,
                mode=TeleporterShuffleMode.ONE_WAY_ANYTHING,
            ),
            translator_configuration=new_gate)

        preset = dataclasses.replace(default_echoes_preset.fork(), configuration=layout_config)

    else:
        preset = default_echoes_preset

    state: dict = {
        "actions": [
            "Temple Grounds/Landing Site/Save Station"
        ],
        "collected_pickups": {
            'Amber Translator': 0,
            'Annihilator Beam': 0,
            'Boost Ball': 0,
            'Cobalt Translator': 0,
            'Dark Agon Key 1': 0,
            'Dark Agon Key 2': 0,
            'Dark Agon Key 3': 0,
            'Dark Ammo Expansion': 0,
            'Dark Beam': 0,
            'Dark Torvus Key 1': 0,
            'Dark Torvus Key 2': 0,
            'Dark Torvus Key 3': 0,
            'Dark Visor': 0,
            'Darkburst': 0,
            'Echo Visor': 0,
            'Emerald Translator': 0,
            'Energy Tank': 0,
            'Grapple Beam': 0,
            'Gravity Boost': 0,
            'Ing Hive Key 1': 0,
            'Ing Hive Key 2': 0,
            'Ing Hive Key 3': 0,
            'Light Ammo Expansion': 0,
            'Light Beam': 0,
            'Missile Expansion': 0,
            'Missile Launcher': 0,
            'Morph Ball Bomb': 0,
            'Power Bomb': 0,
            'Power Bomb Expansion': 0,
            'Progressive Suit': 0,
            'Screw Attack': 0,
            'Seeker Launcher': 0,
            'Sky Temple Key 1': 0,
            'Sky Temple Key 2': 0,
            'Sky Temple Key 3': 0,
            'Sky Temple Key 4': 0,
            'Sky Temple Key 5': 0,
            'Sky Temple Key 6': 0,
            'Sky Temple Key 7': 0,
            'Sky Temple Key 8': 0,
            'Sky Temple Key 9': 0,
            'Sonic Boom': 0,
            'Space Jump Boots': 1,
            'Spider Ball': 0,
            'Sunburst': 0,
            'Super Missile': 0,
            'Violet Translator': 0,
        },
        "elevators": [
            {'data': None,
             'teleporter': {'area_name': 'Transport to Temple Grounds',
                            'node_name': 'Elevator to Temple Grounds - Transport to Agon Wastes',
                            'world_name': 'Agon Wastes'}},
            {'data': None,
             'teleporter': {'area_name': 'Transport to Torvus Bog',
                            'node_name': 'Elevator to Torvus Bog - Transport to Agon Wastes',
                            'world_name': 'Agon Wastes'}},
            {'data': None,
             'teleporter': {'area_name': 'Transport to Sanctuary Fortress',
                            'node_name': 'Elevator to Sanctuary Fortress - Transport to Agon Wastes',
                            'world_name': 'Agon Wastes'}},
            {'data': None,
             'teleporter': {'area_name': 'Temple Transport C',
                            'node_name': 'Elevator to Temple Grounds - Temple Transport C',
                            'world_name': 'Great Temple'}},
            {'data': None,
             'teleporter': {'area_name': 'Temple Transport A',
                            'node_name': 'Elevator to Temple Grounds - Temple Transport A',
                            'world_name': 'Great Temple'}},
            {'data': None,
             'teleporter': {'area_name': 'Temple Transport B',
                            'node_name': 'Elevator to Temple Grounds - Temple Transport B',
                            'world_name': 'Great Temple'}},
            {'data': None,
             'teleporter': {'area_name': 'Transport to Temple Grounds',
                            'node_name': 'Elevator to Temple Grounds - Transport to Sanctuary Fortress',
                            'world_name': 'Sanctuary Fortress'}},
            {'data': None,
             'teleporter': {'area_name': 'Transport to Agon Wastes',
                            'node_name': 'Elevator to Agon Wastes - Transport to Sanctuary Fortress',
                            'world_name': 'Sanctuary Fortress'}},
            {'data': None,
             'teleporter': {'area_name': 'Transport to Torvus Bog',
                            'node_name': 'Elevator to Torvus Bog - Transport to Sanctuary Fortress',
                            'world_name': 'Sanctuary Fortress'}},
            {'data': None,
             'teleporter': {'area_name': 'Transport to Agon Wastes',
                            'node_name': 'Elevator to Agon Wastes - Transport to Temple Grounds',
                            'world_name': 'Temple Grounds'}},
            {'data': None,
             'teleporter': {'area_name': 'Temple Transport B',
                            'node_name': 'Elevator to Great Temple - Temple Transport B',
                            'world_name': 'Temple Grounds'}},
            {'data': None,
             'teleporter': {'area_name': 'Transport to Sanctuary Fortress',
                            'node_name': 'Elevator to Sanctuary Fortress - Transport to Temple Grounds',
                            'world_name': 'Temple Grounds'}},
            {'data': None,
             'teleporter': {'area_name': 'Temple Transport A',
                            'node_name': 'Elevator to Great Temple - Temple Transport A',
                            'world_name': 'Temple Grounds'}},
            {'data': None,
             'teleporter': {'area_name': 'Transport to Torvus Bog',
                            'node_name': 'Elevator to Torvus Bog - Transport to Temple Grounds',
                            'world_name': 'Temple Grounds'}},
            {'data': None,
             'teleporter': {'area_name': 'Temple Transport C',
                            'node_name': 'Elevator to Great Temple - Temple Transport C',
                            'world_name': 'Temple Grounds'}},
            {'data': None,
             'teleporter': {'area_name': 'Transport to Sanctuary Fortress',
                            'node_name': 'Elevator to Sanctuary Fortress - Transport to Torvus Bog',
                            'world_name': 'Torvus Bog'}},
            {'data': None,
             'teleporter': {'area_name': 'Transport to Temple Grounds',
                            'node_name': 'Elevator to Temple Grounds - Transport to Torvus Bog',
                            'world_name': 'Torvus Bog'}},
            {'data': None,
             'teleporter': {'area_name': 'Transport to Agon Wastes',
                            'node_name': 'Elevator to Agon Wastes - Transport to Torvus Bog',
                            'world_name': 'Torvus Bog'}}
        ],
        "configurable_nodes": {
            'Agon Wastes/Mining Plaza/Translator Gate': None,
            'Agon Wastes/Mining Station A/Translator Gate': None,
            'Great Temple/Temple Sanctuary/Transport A Translator Gate': None,
            'Great Temple/Temple Sanctuary/Transport B Translator Gate': None,
            'Great Temple/Temple Sanctuary/Transport C Translator Gate': None,
            'Sanctuary Fortress/Reactor Core/Translator Gate': None,
            'Sanctuary Fortress/Sanctuary Temple/Translator Gate': None,
            'Temple Grounds/GFMC Compound/Translator Gate': None,
            'Temple Grounds/Hive Access Tunnel/Translator Gate': None,
            'Temple Grounds/Hive Transport Area/Translator Gate': None,
            'Temple Grounds/Industrial Site/Translator Gate': None,
            'Temple Grounds/Meeting Grounds/Translator Gate': None,
            'Temple Grounds/Path of Eyes/Translator Gate': None,
            'Temple Grounds/Temple Assembly Site/Translator Gate': None,
            'Torvus Bog/Great Bridge/Translator Gate': None,
            'Torvus Bog/Torvus Temple/Elevator Translator Scan': None,
            'Torvus Bog/Torvus Temple/Translator Gate': None,
        },
        "starting_location": {'world_name': 'Temple Grounds', 'area_name': 'Landing Site'}
    }

    if shuffle_advanced:
        for elevator in state["elevators"]:
            if elevator["teleporter"]["node_name"] == "Elevator to Sanctuary Fortress - Transport to Agon Wastes":
                elevator["data"] = {'area_name': "Agon Energy Controller", 'world_name': "Agon Wastes"}
        state["configurable_nodes"]['Temple Grounds/Hive Access Tunnel/Translator Gate'] = "violet"
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
