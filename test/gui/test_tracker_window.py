import json
from pathlib import Path

import pytest

from randovania.gui import tracker_window
from randovania.layout.layout_configuration import LayoutConfiguration


@pytest.fixture(name="layout_config")
def _layout_config():
    return LayoutConfiguration.default()


def test_load_previous_state_no_previous_layout(tmpdir, layout_config):
    # Run
    result = tracker_window._load_previous_state(Path(tmpdir), layout_config)

    # Assert
    assert result is None


def test_load_previous_state_previous_layout_not_json(tmpdir, layout_config):
    # Setup
    tmpdir.join("layout_configuration.json").write_text("this is not a json", "utf-8")

    # Run
    result = tracker_window._load_previous_state(Path(tmpdir), layout_config)

    # Assert
    assert result is None


def test_load_previous_state_previous_layout_not_layout(tmpdir, layout_config):
    # Setup
    tmpdir.join("layout_configuration.json").write_text(json.dumps({"trick_level": "foo"}), "utf-8")
    tmpdir.join("state.json").write_text("[]", "utf-8")

    # Run
    result = tracker_window._load_previous_state(Path(tmpdir), layout_config)

    # Assert
    assert result is None


def test_load_previous_state_missing_state(tmpdir, layout_config):
    # Setup
    tmpdir.join("layout_configuration.json").write_text(json.dumps(layout_config.as_json), "utf-8")

    # Run
    result = tracker_window._load_previous_state(Path(tmpdir), layout_config)

    # Assert
    assert result is None


def test_load_previous_state_invalid_state(tmpdir, layout_config):
    # Setup
    tmpdir.join("layout_configuration.json").write_text(json.dumps(layout_config.as_json), "utf-8")
    tmpdir.join("state.json").write_text("", "utf-8")

    # Run
    result = tracker_window._load_previous_state(Path(tmpdir), layout_config)

    # Assert
    assert result is None


def test_load_previous_state_success(tmpdir, layout_config):
    # Setup
    data = {"asdf": 5, "zxcv": 123}
    tmpdir.join("layout_configuration.json").write_text(json.dumps(layout_config.as_json), "utf-8")
    tmpdir.join("state.json").write_text(json.dumps(data), "utf-8")

    # Run
    result = tracker_window._load_previous_state(Path(tmpdir), layout_config)

    # Assert
    assert result == data


def test_window_creation(skip_qtbot, tmpdir, layout_config):
    # Setup

    # Run
    window = tracker_window.TrackerWindow(Path(tmpdir), layout_config)
    skip_qtbot.add_widget(window)
    window.reset()

    # Assert
    assert window.state_for_current_configuration() is not None
