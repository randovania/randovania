import asyncio

from PySide2.QtWidgets import QDialog

from randovania.gui.generated.background_process_dialog_ui import Ui_BackgroundProcessDialog
from randovania.gui.lib import common_qt_lib, async_dialog
from randovania.gui.lib.background_task_mixin import BackgroundTaskMixin


class BackgroundProcessDialog(QDialog, BackgroundTaskMixin, Ui_BackgroundProcessDialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)

        self.background_tasks_button_lock_signal.connect(self.update_button_label)
        self.progress_update_signal.connect(self.update_progress)
        self.update_button.clicked.connect(self.on_button_press)

    def on_button_press(self):
        if self.has_background_process:
            self.stop_background_process()
        else:
            self.accept()

    def update_button_label(self, value: bool):
        self.update_button.setText("Close" if value else "Cancel")

    def update_progress(self, message: str, percentage: int):
        self.progress_label.setText(message)
        if "Aborted" in message:
            percentage = 0
        if percentage >= 0:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(percentage)
        else:
            self.progress_bar.setRange(0, 0)

    async def run_in_background_async_then_close(self, *args, **kwargs):
        result = await self.run_in_background_async(*args, **kwargs)
        self.accept()
        return result

    @classmethod
    async def open_for_background_task(cls, target, starting_message: str):
        dialog = cls()
        result = await asyncio.gather(
            dialog.run_in_background_async_then_close(target, starting_message),
            async_dialog.execute_dialog(dialog)
        )
        return result[0]
