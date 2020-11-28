import copy
import dataclasses
import json
from pathlib import Path

import pytest

from randovania.gui import tracker_window
from randovania.layout.elevators import LayoutElevators
from randovania.layout.translator_configuration import LayoutTranslatorRequirement


@pytest.fixture(params=[{},
                        {"elevators": LayoutElevators.ONE_WAY_ANYTHING,
                         "translator_configuration": True}],
                name="layout_config")
def _layout_config(request, default_layout_configuration):
    if "translator_configuration" in request.param:
        translator_requirement = copy.copy(default_layout_configuration.translator_configuration.translator_requirement)
        for gate in translator_requirement.keys():
            translator_requirement[gate] = LayoutTranslatorRequirement.RANDOM
            break

        new_gate = dataclasses.replace(default_layout_configuration.translator_configuration,
                                       translator_requirement=translator_requirement)
        request.param["translator_configuration"] = new_gate
    return dataclasses.replace(default_layout_configuration, **request.param)


def test_load_previous_state_no_previous_layout(tmp_path: Path, default_layout_configuration):
    # Run
    result = tracker_window._load_previous_state(tmp_path, default_layout_configuration)

    # Assert
    assert result is None


def test_load_previous_state_previous_layout_not_json(tmp_path: Path, default_layout_configuration):
    # Setup
    tmp_path.joinpath("layout_configuration.json").write_text("this is not a json")

    # Run
    result = tracker_window._load_previous_state(tmp_path, default_layout_configuration)

    # Assert
    assert result is None


def test_load_previous_state_previous_layout_not_layout(tmp_path: Path, default_layout_configuration):
    # Setup
    tmp_path.joinpath("layout_configuration.json").write_text(json.dumps({"trick_level": "foo"}))
    tmp_path.joinpath("state.json").write_text("[]")

    # Run
    result = tracker_window._load_previous_state(tmp_path, default_layout_configuration)

    # Assert
    assert result is None


def test_load_previous_state_missing_state(tmp_path: Path, default_layout_configuration):
    # Setup
    tmp_path.joinpath("layout_configuration.json").write_text(json.dumps(default_layout_configuration.as_json))

    # Run
    result = tracker_window._load_previous_state(tmp_path, default_layout_configuration)

    # Assert
    assert result is None


def test_load_previous_state_invalid_state(tmp_path: Path, default_layout_configuration):
    # Setup
    tmp_path.joinpath("layout_configuration.json").write_text(json.dumps(default_layout_configuration.as_json))
    tmp_path.joinpath("state.json").write_text("")

    # Run
    result = tracker_window._load_previous_state(tmp_path, default_layout_configuration)

    # Assert
    assert result is None


def test_load_previous_state_success(tmp_path: Path, default_layout_configuration):
    # Setup
    data = {"asdf": 5, "zxcv": 123}
    tmp_path.joinpath("layout_configuration.json").write_text(json.dumps(default_layout_configuration.as_json))
    tmp_path.joinpath("state.json").write_text(json.dumps(data))

    # Run
    result = tracker_window._load_previous_state(tmp_path, default_layout_configuration)

    # Assert
    assert result == data


@pytest.mark.parametrize("shuffle_advanced", [False, True])
def test_apply_previous_state(skip_qtbot, tmp_path: Path, default_layout_configuration, shuffle_advanced):
    if shuffle_advanced:
        translator_requirement = copy.copy(
            default_layout_configuration.translator_configuration.translator_requirement)
        for gate in translator_requirement.keys():
            translator_requirement[gate] = LayoutTranslatorRequirement.RANDOM
            break

        new_gate = dataclasses.replace(default_layout_configuration.translator_configuration,
                                       translator_requirement=translator_requirement)
        layout_config = dataclasses.replace(
            default_layout_configuration,
            elevators=LayoutElevators.ONE_WAY_ANYTHING,
            translator_configuration=new_gate)
    else:
        layout_config = default_layout_configuration

    state = {
        "actions": [
            0,
            4
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
        "elevators": {
            '122': None,
            '1245307': None,
            '1245332': None,
            '129': None,
            '152': None,
            '1572998': None,
            '1638535': None,
            '1966093': None,
            '2097251': None,
            '2162826': None,
            '2949235': None,
            '3342446': None,
            '3538975': None,
            '38': None,
            '393260': None,
            '4522032': None,
            '524321': None,
            '589851': None,
        },
        "translator_gates": {
            "0": None,
            '1': None,
            '10': None,
            '11': None,
            '12': None,
            '13': None,
            '14': None,
            '15': None,
            '16': None,
            '2': None,
            '3': None,
            '4': None,
            '5': None,
            '6': None,
            '7': None,
            '8': None,
            '9': None,
        },
        "starting_location": {
            "world_asset_id": 1006255871,
            "area_asset_id": 1655756413
        }
    }
    if shuffle_advanced:
        state["elevators"]['2949235'] = {'area_asset_id': 50083607, 'world_asset_id': 1119434212}
        state["translator_gates"]['0'] = 97
    tmp_path.joinpath("layout_configuration.json").write_text(json.dumps(layout_config.as_json), "utf-8")
    tmp_path.joinpath("state.json").write_text(json.dumps(state), "utf-8")

    # Run
    window = tracker_window.TrackerWindow(tmp_path, layout_config)
    skip_qtbot.add_widget(window)

    # Assert
    assert window.state_for_current_configuration() is not None
    persisted_data = json.loads(tmp_path.joinpath("state.json").read_text("utf-8"))
    assert persisted_data == state

    window.reset()
    window.persist_current_state()

    persisted_data = json.loads(tmp_path.joinpath("state.json").read_text("utf-8"))
    assert persisted_data != state
