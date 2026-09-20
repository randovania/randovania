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
from randovania.network_common.async_race_room import race_uses_teams

if TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.options import Options
    from randovania.layout.layout_description import LayoutDescription
    from randovania.layout.versioned_preset import VersionedPreset
    from randovania.network_common.async_race_room import AsyncRaceSettings


class AsyncRaceCreationDialog(QtWidgets.QDialog, GenerateGameMixin, BackgroundTaskMixin):
    ui: Ui_AsyncRaceCreationDialog
    selected_presets: list[VersionedPreset]
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
    ) -> None:
        super().__init__(parent)
        self.ui = Ui_AsyncRaceCreationDialog()
        self.ui.setupUi(self)

        self._window_manager = window_manager
        self._options = options
        self.failure_handler = GenerationFailureHandler(self)
        self._background_task = self
        self.selected_presets = []

        self.progress_update_signal.connect(self.update_progress)

        self.ui.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText("Generate then create")
        self.ui.button_box.accepted.connect(self._generate_and_accept)
        self.ui.button_box.rejected.connect(self._on_rejected_button)

        self.ui.preset_button.clicked.connect(self._on_add_world_slot)
        self.ui.change_preset_button.clicked.connect(self._on_change_preset_slot)
        self.ui.remove_world_button.clicked.connect(self._on_remove_world)
        self.ui.world_list.itemSelectionChanged.connect(self._update_world_buttons)

        self.ui.settings_widget.Changed.connect(self._post_validate)
        self._update_world_list()
        self.ui.settings_widget.validate()

    @property
    def world_count(self) -> int:
        return len(self.selected_presets)

    def _uses_teams(self, world_count: int | None = None) -> bool:
        """
        Whether the room being created is hosted in a multiplayer session, and so played in teams.
        """
        if world_count is None:
            world_count = self.world_count
        return race_uses_teams(world_count, self.ui.settings_widget.allow_coop)

    @staticmethod
    def _is_multiworld_compatible(preset: VersionedPreset) -> bool:
        """Whether a world with this preset could be part of a multiplayer session."""
        return preset.game.data.defaults_available_in_game_sessions and not (
            preset.get_preset().settings_incompatible_with_multiworld()
        )

    @property
    def _worlds_allow_multiworld(self) -> bool:
        """
        Whether the worlds picked so far still allow this race to become a multiworld one.
        """
        return all(self._is_multiworld_compatible(preset) for preset in self.selected_presets)

    def _world_problems(self) -> Iterator[str]:
        """Why each of the selected worlds, if any, rules out multiworld."""
        for order, preset in enumerate(self.selected_presets):
            if not preset.game.data.defaults_available_in_game_sessions:
                yield f"World {order + 1}: {preset.game.long_name} does not support multiworld."
            elif incompatible := preset.get_preset().settings_incompatible_with_multiworld():
                yield f"World {order + 1}: {', '.join(incompatible)}"

    def _incompatible_world_reason(self) -> str:
        """The first reason the selected worlds rule out multiworld, for use as a tooltip."""
        return next(self._world_problems(), "")

    def _allowed_games(self, uses_teams: bool) -> list[RandovaniaGame]:
        """
        The games offered for a new world. A race hosted in a multiplayer session is limited to the
        games that support one, exactly like multiplayer sessions themselves are.
        """
        return [
            game
            for game in RandovaniaGame.sorted_all_games()
            if game.data.development_state.can_view()
            and (game.data.defaults_available_in_game_sessions or not uses_teams)
        ]

    def _multiworld_messages(self) -> list[str]:
        """
        Every reason the selected worlds can't be raced in a multiplayer session, for a race that
        needs one. Empty for a race played alone, where no world has to support multiworld.
        """
        if not self._uses_teams():
            return []

        return list(self._world_problems())

    def _update_world_list(self) -> None:
        """Refreshes the world list and everything that depends on how many worlds there are."""
        selected_row = self.ui.world_list.currentRow()

        self.ui.world_list.clear()
        for order, preset in enumerate(self.selected_presets):
            self.ui.world_list.addItem(f"World {order + 1}: {preset.game.long_name} - {preset.name}")

        if self.selected_presets:
            self.ui.world_list.setCurrentRow(min(max(selected_row, 0), len(self.selected_presets) - 1))

        self.ui.settings_widget.set_world_count(self.world_count)
        self.ui.settings_widget.set_multiworld_allowed(self._worlds_allow_multiworld)
        self._update_world_buttons()
        self.ui.settings_widget.validate()

    def _update_preset_label(self, problems: list[str]) -> None:
        if problems:
            text = "These worlds can't be used by a race played in teams:\n" + "\n".join(problems)
        elif not self.selected_presets:
            text = "No Preset Selected"
        elif not self._worlds_allow_multiworld:
            text = f"{self._incompatible_world_reason()}\nThis race can only be played alone, in a single world."
        elif self.world_count > 1:
            text = "Each world keeps its own preset. Players on a team claim one world each."
        else:
            text = "Add another world to make this a multiworld race, played by teams."

        self.ui.preset_label.setText(text)

    def _update_world_buttons(self) -> None:
        has_selection = 0 <= self.ui.world_list.currentRow() < self.world_count
        self.ui.change_preset_button.setEnabled(has_selection)
        self.ui.remove_world_button.setEnabled(has_selection)

        can_add_world = self._worlds_allow_multiworld
        self.ui.preset_button.setEnabled(can_add_world)
        self.ui.preset_button.setToolTip("" if can_add_world else self._incompatible_world_reason())

    def _on_remove_world(self) -> None:
        """Called when the `Remove world` button is pressed."""
        row = self.ui.world_list.currentRow()
        if 0 <= row < self.world_count:
            self.selected_presets.pop(row)
            self._update_world_list()

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
    async def _on_add_world_slot(self) -> None:
        await self._on_select_preset(replace_row=None)

    @asyncSlot()
    async def _on_change_preset_slot(self) -> None:
        row = self.ui.world_list.currentRow()
        if 0 <= row < self.world_count:
            await self._on_select_preset(replace_row=row)

    async def _on_select_preset(self, replace_row: int | None) -> None:
        if self._preset_selection_dialog is not None:
            self._preset_selection_dialog.raise_()
            return

        world_count_after = self.world_count + (1 if replace_row is None else 0)
        needs_multiworld = world_count_after > 1

        dialog = SelectPresetDialog(
            self._window_manager,
            self._options,
            for_multiworld=needs_multiworld,
            allowed_games=self._allowed_games(needs_multiworld),
        )
        try:
            self._preset_selection_dialog = dialog
            if await async_dialog.execute_dialog(dialog) == QtWidgets.QDialog.DialogCode.Accepted:
                selected_preset = dialog.selected_preset
                assert selected_preset is not None
                if replace_row is None:
                    self.selected_presets.append(selected_preset)
                else:
                    self.selected_presets[replace_row] = selected_preset
                self._update_world_list()
        finally:
            self._preset_selection_dialog = None

    def _post_validate(self, valid: bool) -> None:
        problems = self._multiworld_messages()
        self._update_preset_label(problems)

        self.ui.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setEnabled(
            valid and bool(self.selected_presets) and not problems and not self._background_task.has_background_process
        )

    @property
    def generate_parent_widget(self) -> QtWidgets.QWidget:
        return self

    @asyncSlot()
    async def _generate_and_accept(self) -> None:
        if not self.selected_presets:
            return

        try:
            self._post_validate(False)
            self.layout_description = await self.generate_layout_from_presets(list(self.selected_presets), spoiler=True)
        finally:
            self.ui.settings_widget.validate()

        if self.layout_description is not None:
            self.accept()
