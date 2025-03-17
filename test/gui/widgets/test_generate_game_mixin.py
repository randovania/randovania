from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
from PySide6 import QtWidgets

from randovania.gui.lib.background_task_mixin import BackgroundTaskMixin
from randovania.gui.lib.generation_failure_handling import GenerationFailureHandler
from randovania.gui.widgets.generate_game_mixin import GenerateGameMixin
from randovania.resolver.exceptions import ImpossibleForSolver

if TYPE_CHECKING:
    import pytest_mock


@pytest.mark.parametrize("case", ["success", "ignore-solver", "abort"])
async def test_generate_layout_from_permalink(skip_qtbot, mocker: pytest_mock.MockerFixture, options, case):
    parent = QtWidgets.QWidget()
    skip_qtbot.add_widget(parent)

    with options:
        options.advanced_generate_in_another_process = False

    background_task = MagicMock(spec=BackgroundTaskMixin)
    mock_alert = mocker.patch("randovania.gui.lib.common_qt_lib.alert_user_on_generation")
    mock_dialog = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)

    expected_layout = MagicMock()
    background_task.run_in_background_async.return_value = expected_layout

    if case != "success":
        background_task.run_in_background_async.side_effect = ImpossibleForSolver("Can't", MagicMock(), expected_layout)

    if case == "ignore-solver":
        mock_dialog.return_value = QtWidgets.QMessageBox.StandardButton.Save

    class OurGameWidget(GenerateGameMixin):
        def __init__(self):
            self._background_task = background_task
            self._options = options
            self.failure_handler = MagicMock(spec=GenerationFailureHandler)

        @property
        def generate_parent_widget(self) -> QtWidgets.QWidget:
            return parent

    # Setup
    permalink = MagicMock()
    obj = OurGameWidget()

    # Run
    result = await obj.generate_layout_from_permalink(permalink)

    # Assert
    mock_alert.assert_called_once_with(parent, options)

    if case != "abort":
        assert result is expected_layout
        background_task.progress_update_signal.emit.assert_called_once_with(
            f"Success! (Seed hash: {expected_layout.shareable_hash})", 100
        )
    else:
        assert result is None
        background_task.progress_update_signal.emit.assert_called_once_with("Solver Error", 0)

    if case != "success":
        mock_dialog.assert_awaited_once()
    else:
        mock_dialog.assert_not_called()
