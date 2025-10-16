from __future__ import annotations

import dataclasses
import datetime
import json
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, call

import pytest

from randovania.gui.dialog import preset_history_dialog
from randovania.layout.base.damage_strictness import LayoutDamageStrictness
from randovania.layout.preset import Preset
from randovania.layout.versioned_preset import VersionedPreset

if TYPE_CHECKING:
    import pytest_mock


@pytest.mark.parametrize("broken_original", [False, True])
async def test_select_item(skip_qtbot, default_preset, tmp_path, mocker: pytest_mock.MockerFixture, broken_original):
    # Setup
    mocker.patch(
        "randovania.layout.preset_describer.describe",
        side_effect=[
            [("Header", ["Thing", "Other"])],
            [("Header", ["Thing", "SUPER"])],
        ],
    )

    versioned_preset = VersionedPreset.with_preset(default_preset)
    old_preset = dataclasses.replace(
        default_preset,
        configuration=dataclasses.replace(
            default_preset.configuration,
            damage_strictness=LayoutDamageStrictness.STRICT,
        ),
    )

    if broken_original:
        preset_data = versioned_preset.as_json
        preset_data["schema_version"] = 1
        versioned_preset = VersionedPreset(preset_data)

    preset_manager = MagicMock()
    preset_manager.get_previous_versions.return_value = [
        (datetime.datetime(2020, 10, 1, 10, 20), b"ABCDEF"),
    ]
    preset_manager.get_previous_version.return_value = json.dumps(VersionedPreset.with_preset(old_preset).as_json)

    dialog = preset_history_dialog.PresetHistoryDialog(preset_manager, versioned_preset)
    skip_qtbot.add_widget(dialog)

    # Run
    preset_manager.get_previous_version.assert_called_once_with(versioned_preset, b"ABCDEF")
    assert dialog.version_widget.count() == 2

    # Initially the dialog has nothing selected
    assert dialog.selected_preset() is None
    assert not dialog.accept_button.isEnabled()

    # Select the first row
    dialog.version_widget.setCurrentIndex(dialog.version_widget.model().index(0))
    assert dialog.selected_preset() is None
    assert not dialog.accept_button.isEnabled()
    if broken_original:
        assert dialog.label.text() == (
            "Preset Starter Preset at this version can't be used as it contains the following error:\n"
            "'layout_configuration'"
        )
    else:
        assert dialog.label.text() == "# Starter Preset\n\nBasic preset.\n\n\n\n## Header\n\nThing\n\nOther"

    # Select the second row
    dialog.version_widget.setCurrentIndex(dialog.version_widget.model().index(1))
    assert dialog.selected_preset() == old_preset
    assert dialog.accept_button.isEnabled()
    if broken_original:
        assert dialog.label.text() == "# Starter Preset\n\nBasic preset.\n\n\n\n## Header\n\nThing\n\nOther"
    else:
        assert dialog.label.text() == "@@ -3,4 +3,4 @@\n\n\n \n\n ## Header\n\n Thing\n\n-Other\n\n+SUPER"

    # Export
    mock_prompt = mocker.patch(
        "randovania.gui.lib.file_prompts.prompt_preset", return_value=tmp_path.joinpath("sample.rdvpreset")
    )
    await dialog._export_selected_preset()

    mock_prompt.assert_awaited_once_with(dialog, new_file=True, name="starter-preset.rdvpreset")
    assert tmp_path.joinpath("sample.rdvpreset").is_file()


def test_get_old_preset_bad_json():
    assert preset_history_dialog._get_old_preset("{]").startswith("Preset at this version contains json errors:")


def test_get_old_preset_bad_formatting():
    assert preset_history_dialog._get_old_preset('{"name": "theName"}') == (
        "Preset theName at this version can't be used as it contains the following error:\n'layout_configuration'"
    )


def test_calculate_previous_versions(mocker):
    preset_manager = MagicMock()
    preset_manager.get_previous_versions.return_value = [
        (datetime.datetime(2020, 1, 1, 0, 0), b"0"),
        (datetime.datetime(2020, 2, 1, 0, 0), b"1"),
        (datetime.datetime(2020, 3, 1, 0, 0), b"2"),
    ]

    preset_ref = MagicMock()
    mock_old = mocker.patch(
        "randovania.gui.dialog.preset_history_dialog._get_old_preset",
        side_effect=[
            "Invalid preset",
            preset_a := MagicMock(spec=Preset),
            preset_b := MagicMock(spec=Preset),
        ],
    )
    mock_describe = mocker.patch(
        "randovania.gui.dialog.preset_history_dialog._describe_preset",
        return_value=[
            "Part1",
            "Part2",
        ],
    )

    # Run
    result = list(preset_history_dialog._calculate_previous_versions(preset_manager, preset_ref, ()))

    # Assert
    preset_manager.get_previous_versions.assert_called_once_with(preset_ref)
    preset_manager.get_previous_version.assert_has_calls(
        [
            call(preset_ref, b"0"),
            call(preset_ref, b"1"),
            call(preset_ref, b"2"),
        ]
    )
    mock_old.assert_has_calls([call(preset_manager.get_previous_version.return_value)] * 3)
    mock_describe.assert_has_calls([call(preset_a), call(preset_b)])

    assert result == [
        (datetime.datetime(2020, 2, 1, 0, 0), preset_a, ("Part1", "Part2")),
    ]
