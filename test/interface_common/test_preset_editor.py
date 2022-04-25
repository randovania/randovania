import dataclasses
from unittest.mock import MagicMock

import pytest

from randovania.games.prime2.layout.echoes_configuration import LayoutSkyTempleKeyMode
from randovania.interface_common.preset_editor import PresetEditor


@pytest.fixture(name="editor")
def _editor() -> PresetEditor:
    return PresetEditor(MagicMock())


_sample_layout_configurations = [
    {
        "sky_temple_keys": LayoutSkyTempleKeyMode.default(),
        "menu_mod": False,
    }
]


@pytest.fixture(params=_sample_layout_configurations, name="initial_layout_configuration_params")
def _initial_layout_configuration_params(request) -> dict:
    return request.param


@pytest.mark.parametrize("menu_mod", [False, True])
def test_edit_menu_mod(editor: PresetEditor,
                       initial_layout_configuration_params: dict,
                       default_echoes_configuration,
                       menu_mod):
    # Setup
    editor._configuration = dataclasses.replace(default_echoes_configuration,
                                                **initial_layout_configuration_params)
    editor._nested_autosave_level = 1

    # Run
    initial_layout_configuration_params["menu_mod"] = menu_mod
    editor.set_configuration_field("menu_mod", menu_mod)

    # Assert
    assert editor.configuration == dataclasses.replace(default_echoes_configuration,
                                                       **initial_layout_configuration_params)
