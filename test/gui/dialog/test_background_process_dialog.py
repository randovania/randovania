import pytest

from randovania.gui.dialog.background_process_dialog import BackgroundProcessDialog


def invoke_callable(target):
    target()


@pytest.mark.asyncio
async def test_open_for_background_task(skip_qtbot, mocker):
    mocker.patch("randovania.gui.dialog.background_process_dialog.BackgroundProcessDialog._start_thread_for",
                 side_effect=invoke_callable)

    def work(progress_update):
        progress_update("Hello", 1)
        return 5

    result = await BackgroundProcessDialog.open_for_background_task(work, "Starting")
    assert result == 5
