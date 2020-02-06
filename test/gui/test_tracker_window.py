import json
from pathlib import Path

import pytest

from randovania.gui import tracker_window
from randovania.layout.layout_configuration import LayoutConfiguration


@pytest.fixture(name="layout_config")
def _layout_config(default_layout_configuration):
    return default_layout_configuration


def test_load_previous_state_no_previous_layout(tmp_path: Path, layout_config):
    # Run
    result = tracker_window._load_previous_state(tmp_path, layout_config)

    # Assert
    assert result is None


def test_load_previous_state_previous_layout_not_json(tmp_path: Path, layout_config):
    # Setup
    tmp_path.joinpath("layout_configuration.json").write_text("this is not a json")

    # Run
    result = tracker_window._load_previous_state(tmp_path, layout_config)

    # Assert
    assert result is None


def test_load_previous_state_previous_layout_not_layout(tmp_path: Path, layout_config):
    # Setup
    tmp_path.joinpath("layout_configuration.json").write_text(json.dumps({"trick_level": "foo"}))
    tmp_path.joinpath("state.json").write_text("[]")

    # Run
    result = tracker_window._load_previous_state(tmp_path, layout_config)

    # Assert
    assert result is None


def test_load_previous_state_missing_state(tmp_path: Path, layout_config):
    # Setup
    tmp_path.joinpath("layout_configuration.json").write_text(json.dumps(layout_config.as_json))

    # Run
    result = tracker_window._load_previous_state(tmp_path, layout_config)

    # Assert
    assert result is None


def test_load_previous_state_invalid_state(tmp_path: Path, layout_config):
    # Setup
    tmp_path.joinpath("layout_configuration.json").write_text(json.dumps(layout_config.as_json))
    tmp_path.joinpath("state.json").write_text("")

    # Run
    result = tracker_window._load_previous_state(tmp_path, layout_config)

    # Assert
    assert result is None


def test_load_previous_state_success(tmp_path: Path, layout_config):
    # Setup
    data = {"asdf": 5, "zxcv": 123}
    tmp_path.joinpath("layout_configuration.json").write_text(json.dumps(layout_config.as_json))
    tmp_path.joinpath("state.json").write_text(json.dumps(data))

    # Run
    result = tracker_window._load_previous_state(tmp_path, layout_config)

    # Assert
    assert result == data


def test_window_creation(skip_qtbot, tmp_path: Path, layout_config):
    # Setup

    # Run
    window = tracker_window.TrackerWindow(tmp_path, layout_config)
    skip_qtbot.add_widget(window)
    window.reset()

    # Assert
    assert window.state_for_current_configuration() is not None
