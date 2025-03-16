from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING

from PySide6 import QtWidgets
from qasync import asyncSlot

from randovania import monitoring
from randovania.gui.generated.generate_game_widget_ui import Ui_GenerateGameWidget
from randovania.gui.lib.common_qt_lib import alert_user_on_generation
from randovania.gui.lib.generation_failure_handling import GenerationFailureHandler
from randovania.gui.widgets.generate_game_mixin import GenerateGameMixin

if TYPE_CHECKING:
    from pathlib import Path

    from randovania.game.game_enum import RandovaniaGame
    from randovania.gui.lib.background_task_mixin import BackgroundTaskMixin
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.options import Options
    from randovania.layout.layout_description import LayoutDescription
    from randovania.layout.permalink import Permalink
    from randovania.layout.versioned_preset import VersionedPreset


class RetryGeneration(Exception):
    pass


def persist_layout(history_dir: Path, description: LayoutDescription) -> None:
    history_dir.mkdir(parents=True, exist_ok=True)

    games = "-".join(sorted(game.short_name for game in description.all_games))

    date_format = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    file_path = history_dir.joinpath(
        f"{date_format}_{games}_{description.shareable_word_hash}.{description.file_extension()}"
    )
    description.save_to_file(file_path)


class GenerateGameWidget(QtWidgets.QWidget, Ui_GenerateGameWidget, GenerateGameMixin):
    _background_task: BackgroundTaskMixin
    _window_manager: WindowManager
    _options: Options
    game: RandovaniaGame

    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)
        self.failure_handler = GenerationFailureHandler(self)

    def setup_ui(
        self,
        game: RandovaniaGame,
        window_manager: WindowManager,
        background_task: BackgroundTaskMixin,
        options: Options,
    ) -> None:
        self._window_manager = window_manager
        self._background_task = background_task
        self._options = options
        self.game = game

        self.select_preset_widget.setup_ui(game, self._window_manager, self._options)

        # Progress
        self._background_task.background_tasks_button_lock_signal.connect(self.enable_buttons_with_background_tasks)

        self.num_worlds_spin_box.setVisible(self._window_manager.is_preview_mode)
        self.create_generate_no_retry_button.setVisible(self._window_manager.is_preview_mode)

        # Signals
        self.create_generate_button.clicked.connect(self.generate_new_layout_regular)
        self.create_generate_no_retry_button.clicked.connect(self.generate_new_layout_no_retry)
        self.create_generate_race_button.clicked.connect(self.generate_new_layout_race)
        self.select_preset_widget.CanGenerate.connect(self._on_can_generate)

    def enable_buttons_with_background_tasks(self, value: bool) -> None:
        self.create_generate_button.setEnabled(value)
        self.create_generate_race_button.setEnabled(value)

    @property
    def preset(self) -> VersionedPreset:
        preset = self.select_preset_widget.preset
        if preset is None:
            preset = self._window_manager.preset_manager.default_preset_for_game(self.game)
        return preset

    # Generate seed

    async def generate_new_layout(self, spoiler: bool, retries: int | None = None) -> LayoutDescription | None:
        """
        Generates a LayoutDescription based on the selected preset.
        """
        return await self.generate_layout_from_preset(
            self.preset,
            spoiler=spoiler,
            num_worlds=self.num_worlds_spin_box.value(),
            retries=retries,
        )

    @asyncSlot()
    async def generate_new_layout_regular(self) -> None:
        monitoring.metrics.incr("gui_generate_plain", tags={"game": self.game.value})
        return await self.generate_new_layout(spoiler=True)

    @asyncSlot()
    async def generate_new_layout_no_retry(self) -> None:
        monitoring.metrics.incr("gui_generate_no_retry", tags={"game": self.game.value})
        return await self.generate_new_layout(spoiler=True, retries=0)

    @asyncSlot()
    async def generate_new_layout_race(self) -> None:
        monitoring.metrics.incr("gui_generate_race", tags={"game": self.game.value})
        return await self.generate_new_layout(spoiler=False)

    @property
    def generate_parent_widget(self) -> QtWidgets.QWidget:
        return self

    async def generate_layout_from_permalink(self, permalink: Permalink, retries: int | None = None) -> None:
        if self._window_manager.is_preview_mode:
            logging.info(f"Permalink: {permalink.as_base64_str}")

        layout = await super().generate_layout_from_permalink(permalink, retries)
        alert_user_on_generation(self, self._options)

        if layout is not None:
            persist_layout(self._options.game_history_path, layout)
            self._window_manager.open_game_details(layout)

    def on_options_changed(self, options: Options) -> None:
        self.select_preset_widget.on_options_changed(options)

    def on_new_preset(self, preset: VersionedPreset) -> None:
        self.select_preset_widget.on_new_preset(preset)

    def _on_can_generate(self, can_generate: bool) -> None:
        for btn in [
            self.create_generate_button,
            self.create_generate_race_button,
            self.create_generate_no_retry_button,
        ]:
            btn.setEnabled(can_generate)
