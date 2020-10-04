import pytest

from randovania.gui.dialog.background_process_dialog import BackgroundProcessDialog


@pytest.mark.asyncio
async def test_open_for_background_task(skip_qtbot):
    def work(progress_update):
        progress_update("Hello", 1)
        return 5

    result = await BackgroundProcessDialog.open_for_background_task(work, "Starting")
    assert result == 5
