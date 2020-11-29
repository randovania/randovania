import dataclasses
from unittest.mock import MagicMock

import pytest

from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.echoes_configuration import LayoutSkyTempleKeyMode
from randovania.layout.elevators import LayoutElevators


@pytest.fixture(name="editor")
def _editor() -> PresetEditor:
    return PresetEditor(MagicMock())


_sample_layout_configurations = [
    {
        "sky_temple_keys": LayoutSkyTempleKeyMode.default(),
        "elevators": LayoutElevators.TWO_WAY_RANDOMIZED,
    }
]


@pytest.fixture(params=_sample_layout_configurations, name="initial_layout_configuration_params")
def _initial_layout_configuration_params(request) -> dict:
    return request.param


@pytest.mark.parametrize("skip_final_bosses", [False, True])
def test_edit_skip_final_bosses(editor: PresetEditor,
                                initial_layout_configuration_params: dict,
                                default_layout_configuration,
                                skip_final_bosses):
    # Setup
    editor._configuration = dataclasses.replace(default_layout_configuration,
                                                **initial_layout_configuration_params)
    editor._nested_autosave_level = 1

    # Run
    initial_layout_configuration_params["skip_final_bosses"] = skip_final_bosses
    editor.set_configuration_field("skip_final_bosses", skip_final_bosses)

    # Assert
    assert editor.configuration == dataclasses.replace(default_layout_configuration,
                                                       **initial_layout_configuration_params)
