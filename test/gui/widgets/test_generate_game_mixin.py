from __future__ import annotations

import asyncio
import contextlib
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
from PySide6 import QtWidgets

from randovania.gui.lib.background_task_mixin import BackgroundTaskMixin
from randovania.gui.lib.generation_failure_handling import GenerationFailureHandler
from randovania.gui.widgets.generate_game_mixin import GenerateGameMixin, RetryGeneration
from randovania.resolver.exceptions import ImpossibleForSolver

if TYPE_CHECKING:
    import pytest_mock


@pytest.mark.parametrize("case", ["success", "ignore-solver", "abort", "retry", "error", "cancel"])
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

    match case:
        case "success":
            pass

        case "ignore-solver" | "abort" | "retry":
            background_task.run_in_background_async.side_effect = ImpossibleForSolver(
                "Can't", MagicMock(), expected_layout
            )
            _button_for_case = {
                "ignore-solver": QtWidgets.QMessageBox.StandardButton.Save,
                "abort": QtWidgets.QMessageBox.StandardButton.Cancel,
                "retry": QtWidgets.QMessageBox.StandardButton.Retry,
            }
            mock_dialog.return_value = _button_for_case[case]

        case "error":
            background_task.run_in_background_async.side_effect = RuntimeError("an error!")

        case "cancel":
            background_task.run_in_background_async.side_effect = asyncio.exceptions.CancelledError()

    if case == "retry":
        expectation = pytest.raises(RetryGeneration)
    else:
        expectation = contextlib.nullcontext()

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
    with expectation:
        result = await obj.generate_layout_from_permalink(permalink)

    # Assert
    if case != "cancel":
        mock_alert.assert_called_once_with(parent, options)
    else:
        mock_alert.assert_not_called()

    if case != "retry":
        # We don't finish on the retry case
        if case in {"success", "ignore-solver"}:
            assert result is expected_layout
            background_task.progress_update_signal.emit.assert_called_once_with(
                f"Success! (Seed hash: {expected_layout.shareable_hash})", 100
            )
        else:
            assert result is None
            if case == "abort":
                background_task.progress_update_signal.emit.assert_called_once_with("Solver Error", 0)
            elif case == "error":
                obj.failure_handler.handle_exception.assert_called_once()

    if case in {"ignore-solver", "abort", "retry"}:
        mock_dialog.assert_awaited_once()
    else:
        mock_dialog.assert_not_called()
