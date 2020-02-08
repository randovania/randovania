import dataclasses
import json
from pathlib import Path

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import randovania.interface_common.options
import randovania.interface_common.persisted_options
from randovania.interface_common.options import Options, DecodeFailedException
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.layout_configuration import LayoutConfiguration, LayoutElevators, \
    LayoutSkyTempleKeyMode
from randovania.layout.starting_location import StartingLocation
from randovania.layout.trick_level import LayoutTrickLevel, TrickLevelConfiguration


@pytest.fixture(name="editor")
def _editor() -> PresetEditor:
    return PresetEditor(MagicMock())


_sample_layout_configurations = [
    {
        "trick_level_configuration": TrickLevelConfiguration(trick_level),
        "sky_temple_keys": LayoutSkyTempleKeyMode.default(),
        "elevators": LayoutElevators.TWO_WAY_RANDOMIZED,
    }
    for trick_level in [LayoutTrickLevel.NO_TRICKS, LayoutTrickLevel.HARD, LayoutTrickLevel.MINIMAL_RESTRICTIONS]
]


@pytest.fixture(params=_sample_layout_configurations, name="initial_layout_configuration_params")
def _initial_layout_configuration_params(request) -> dict:
    return request.param


@pytest.mark.parametrize("new_trick_level",
                         [LayoutTrickLevel.NO_TRICKS, LayoutTrickLevel.TRIVIAL, LayoutTrickLevel.HYPERMODE])
def test_edit_layout_trick_level(editor: PresetEditor,
                                 initial_layout_configuration_params: dict,
                                 default_layout_configuration,
                                 new_trick_level: LayoutTrickLevel):
    # Setup
    editor._layout_configuration = dataclasses.replace(default_layout_configuration,
                                                       **initial_layout_configuration_params)
    editor._nested_autosave_level = 1

    # Run
    initial_layout_configuration_params["trick_level_configuration"] = TrickLevelConfiguration(new_trick_level)
    editor.set_layout_configuration_field("trick_level_configuration", TrickLevelConfiguration(new_trick_level))

    # Assert
    assert editor.layout_configuration == dataclasses.replace(default_layout_configuration,
                                                              **initial_layout_configuration_params)
