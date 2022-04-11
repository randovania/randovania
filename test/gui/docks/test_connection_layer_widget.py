import dataclasses
from unittest.mock import AsyncMock, ANY

import pytest
from PySide6 import QtWidgets

from randovania.gui.docks.connection_layer_widget import ConnectionLayerWidget
from randovania.layout.base.trick_level import LayoutTrickLevel
from randovania.layout.versioned_preset import VersionedPreset


@pytest.mark.parametrize("preset_state", [0, 1, 2])
async def test_on_load_preset(skip_qtbot, blank_game_description, mocker, preset_state, tmp_path, preset_manager):
    preset_path = tmp_path.joinpath("preset.rdvpreset")

    base_preset = preset_manager.default_preset_for_game(blank_game_description.game).get_preset()
    trick_level = base_preset.configuration.trick_level
    for trick in blank_game_description.resource_database.trick:
        trick_level = trick_level.set_level_for_trick(trick, LayoutTrickLevel.HYPERMODE)

    preset = dataclasses.replace(
        base_preset,
        configuration=dataclasses.replace(base_preset.configuration,
                                          trick_level=trick_level),
    )

    if preset_state > 1:
        VersionedPreset.with_preset(preset).save_to_file(preset_path)

    mock_prompt_preset: AsyncMock = mocker.patch(
        "randovania.gui.lib.file_prompts.prompt_preset",
        return_value=preset_path if preset_state > 0 else None,
    )
    mock_warning: AsyncMock = mocker.patch("randovania.gui.lib.async_dialog.warning")

    root = QtWidgets.QWidget()
    skip_qtbot.addWidget(root)

    widget = ConnectionLayerWidget(root, blank_game_description)

    # Run
    await widget._on_load_preset()

    # Assert
    mock_prompt_preset.assert_awaited_once_with(widget, False)
    if preset_state == 1:
        mock_warning.assert_awaited_once_with(widget, "Invalid preset", ANY)
    else:
        mock_warning.assert_not_awaited()

    for (trick, trick_check), combo in widget.tricks.items():
        assert trick_check.isChecked() == (preset_state == 2)
        assert combo.currentData() == (5 if preset_state == 2 else 0)
