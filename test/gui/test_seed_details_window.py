import pytest
from PySide2 import QtWidgets
from mock import MagicMock, AsyncMock, call

from randovania.gui.seed_details_window import SeedDetailsWindow


@pytest.mark.asyncio
async def test_export_iso(skip_qtbot, mocker):
    # Setup
    mock_execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock,
                                       return_value=QtWidgets.QDialog.Accepted)

    options = MagicMock()
    options.output_directory = None

    window = SeedDetailsWindow(None, options)
    window.layout_description = MagicMock()
    window._player_names = {}
    window.run_in_background_thread = MagicMock()

    # Run
    await window._export_iso()

    # Assert
    mock_execute_dialog.assert_awaited_once()
    window.run_in_background_thread.assert_called_once()


def test_update_layout_description(skip_qtbot, mocker):
    # Setup
    mock_describer = mocker.patch("randovania.gui.lib.preset_describer.describe", return_value=["a", "b", "c", "d"])
    mock_merge = mocker.patch("randovania.gui.lib.preset_describer.merge_categories", return_value="<description>")

    options = MagicMock()
    description = MagicMock()
    description.permalink.player_count = 1
    description.permalink.as_str = "<permalink>"
    description.permalink.spoiler = False

    window = SeedDetailsWindow(None, options)

    # Run
    window.update_layout_description(description)

    # Assert
    mock_describer.assert_called_once_with(description.permalink.get_preset.return_value)
    mock_merge.assert_has_calls([
        call(["a", "c"]),
        call(["b", "d"]),
    ])
