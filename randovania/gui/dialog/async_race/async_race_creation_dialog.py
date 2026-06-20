from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtWidgets
from qasync import asyncSlot

from randovania.game.game_enum import RandovaniaGame
from randovania.gui.dialog.select_preset_dialog import SelectPresetDialog
from randovania.gui.generated.async_race_creation_dialog_ui import Ui_AsyncRaceCreationDialog
from randovania.gui.lib import async_dialog
from randovania.gui.lib.background_task_mixin import BackgroundTaskMixin
from randovania.gui.lib.generation_failure_handling import GenerationFailureHandler
from randovania.gui.widgets.generate_game_mixin import GenerateGameMixin

if TYPE_CHECKING:
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.options import Options
    from randovania.layout.layout_description import LayoutDescription
    from randovania.layout.versioned_preset import VersionedPreset
    from randovania.network_common.async_race_room import AsyncRaceSettings


class AsyncRaceCreationDialog(QtWidgets.QDialog, GenerateGameMixin, BackgroundTaskMixin):
    ui: Ui_AsyncRaceCreationDialog
    selected_preset: VersionedPreset | None = None
    _preset_selection_dialog: SelectPresetDialog | None = None
    layout_description: LayoutDescription | None = None

    _background_task: BackgroundTaskMixin
    _window_manager: WindowManager
    _options: Options

    def __init__(
        self,
        parent: QtWidgets.QWidget,
        window_manager: WindowManager,
        options: Options,
    ):
        super().__init__(parent)
        self.ui = Ui_AsyncRaceCreationDialog()
        self.ui.setupUi(self)

        self._window_manager = window_manager
        self._options = options
        self.failure_handler = GenerationFailureHandler(self)
        self._background_task = self

        self.progress_update_signal.connect(self.update_progress)

        self.ui.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText("Generate then create")
        self.ui.button_box.accepted.connect(self._generate_and_accept)
        self.ui.button_box.rejected.connect(self._on_rejected_button)

        self.ui.preset_button.clicked.connect(self._on_select_preset_slot)

        self.ui.settings_widget.Changed.connect(self._post_validate)
        self.ui.settings_widget.validate()

    def create_settings_object(self) -> AsyncRaceSettings:
        return self.ui.settings_widget.create_settings_object()

    def _on_rejected_button(self) -> None:
        if self.has_background_process:
            self.stop_background_process()
        else:
            reply = QtWidgets.QMessageBox.question(
                self,
                "Close?",
                "Do you want to close the window?",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                QtWidgets.QMessageBox.StandardButton.No,
            )
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                self.reject()

    def update_progress(self, message: str, percentage: int) -> None:
        self.ui.progress_label.setText(message)
        if "Aborted" in message:
            percentage = 0
        if percentage >= 0:
            self.ui.progress_bar.setRange(0, 100)
            self.ui.progress_bar.setValue(percentage)
        else:
            self.ui.progress_bar.setRange(0, 0)

    @asyncSlot()
    async def _on_select_preset_slot(self) -> None:
        await self._on_select_preset()

    async def _on_select_preset(self) -> None:
        if self._preset_selection_dialog is not None:
            self._preset_selection_dialog.raise_()
            return

        dialog = SelectPresetDialog(
            self._window_manager,
            self._options,
            for_multiworld=False,
            allowed_games=[
                game for game in RandovaniaGame.sorted_all_games() if game.data.development_state.can_view()
            ],
        )
        try:
            self._preset_selection_dialog = dialog
            if await async_dialog.execute_dialog(dialog) == QtWidgets.QDialog.DialogCode.Accepted:
                self.selected_preset = dialog.selected_preset
                assert self.selected_preset is not None
                self.ui.preset_label.setText(f"{self.selected_preset.game.long_name}<br />{self.selected_preset.name}")
                self.ui.settings_widget.validate()
        finally:
            self._preset_selection_dialog = None

    def _post_validate(self, valid: bool) -> None:
        self.ui.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setEnabled(
            valid and self.selected_preset is not None and not self._background_task.has_background_process
        )

    @property
    def generate_parent_widget(self) -> QtWidgets.QWidget:
        return self

    @asyncSlot()
    async def _generate_and_accept(self) -> None:
        selected_preset = self.selected_preset
        if selected_preset is None:
            return

        try:
            self._post_validate(False)
            self.layout_description = await self.generate_layout_from_preset(preset=selected_preset, spoiler=True)
        finally:
            self.ui.settings_widget.validate()

        if self.layout_description is not None:
            self.accept()
