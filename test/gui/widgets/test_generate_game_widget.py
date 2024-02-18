from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest

from randovania.gui.lib import async_dialog
from randovania.gui.widgets.generate_game_widget import GenerateGameWidget
from randovania.layout.generator_parameters import GeneratorParameters
from randovania.layout.permalink import Permalink

if TYPE_CHECKING:
    import pytest_mock


@pytest.fixture()
def tab(skip_qtbot, preset_manager, game_enum):
    window_manager = MagicMock()
    window_manager.preset_manager = preset_manager

    widget = GenerateGameWidget()
    skip_qtbot.addWidget(widget)
    widget.setup_ui(game_enum, window_manager, MagicMock(), MagicMock())
    return widget


@pytest.mark.parametrize(
    ("has_unsupported", "abort_generate"),
    [
        (False, False),
        (True, False),
        (True, True),
    ],
)
async def test_generate_new_layout(
    tab: GenerateGameWidget, mocker: pytest_mock.MockerFixture, has_unsupported, abort_generate, is_dev_version
):
    # Setup
    mock_randint = mocker.patch("random.randint", return_value=12341234)
    mock_warning = mocker.patch("randovania.gui.lib.async_dialog.warning")

    versioned_preset = MagicMock()
    versioned_preset.name = "PresetName"
    preset = versioned_preset.get_preset.return_value
    preset.configuration.unsupported_features.return_value = ["Unsup1", "Unsup2"] if has_unsupported else []

    mock_warning.return_value = async_dialog.StandardButton.No if abort_generate else async_dialog.StandardButton.Yes

    tab.select_preset_widget = MagicMock()
    tab.select_preset_widget.preset = versioned_preset
    tab.generate_layout_from_permalink = AsyncMock()

    spoiler = MagicMock(spec=bool)
    retries = MagicMock(spec=int)

    # Run
    await tab.generate_new_layout(spoiler, retries)

    # Assert
    if has_unsupported:
        mock_warning.assert_awaited_once_with(
            tab,
            "Unsupported Features",
            "Preset 'PresetName' uses the unsupported features:\nUnsup1, Unsup2\n\n"
            + (
                "Are you sure you want to continue?"
                if is_dev_version
                else "These features are not available outside of development builds."
            ),
            buttons=(
                async_dialog.StandardButton.Yes | async_dialog.StandardButton.No
                if is_dev_version
                else async_dialog.StandardButton.No
            ),
            default_button=async_dialog.StandardButton.No,
        )
    else:
        mock_warning.assert_not_awaited()

    if abort_generate:
        tab.generate_layout_from_permalink.assert_not_awaited()
        mock_randint.assert_not_called()
    else:
        tab.generate_layout_from_permalink.assert_awaited_once_with(
            permalink=Permalink.from_parameters(
                GeneratorParameters(
                    seed_number=12341234,
                    spoiler=spoiler,
                    presets=[preset],
                )
            ),
            retries=retries,
        )
        mock_randint.assert_called_once_with(0, 2**31)
