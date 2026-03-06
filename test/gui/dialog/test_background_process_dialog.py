from __future__ import annotations

from unittest.mock import AsyncMock

from randovania.gui.dialog.background_process_dialog import BackgroundProcessDialog


async def test_open_for_background_task(skip_qtbot, mocker):
    def on_execute_dialog(dialog):
        skip_qtbot.addWidget(dialog)

    mocker.patch(
        "randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock, side_effect=on_execute_dialog
    )

    # Patch threading.Thread (outside any Qt class MRO) to run the target synchronously
    # instead of spawning a real thread, avoiding class-level patching on Qt classes.
    class _SyncThread:
        def __init__(self, target, **kwargs):
            self._target = target

        def start(self):
            self._target()

    mocker.patch("threading.Thread", _SyncThread)

    def work(progress_update):
        progress_update("Hello", 1)
        return 5

    result = await BackgroundProcessDialog.open_for_background_task(work, "Starting")
    assert result == 5
