from __future__ import annotations

import asyncio
import datetime
import logging
import random
from typing import TYPE_CHECKING

from PySide6 import QtWidgets
from qasync import asyncSlot

import randovania
from randovania import monitoring
from randovania.gui.generated.generate_game_widget_ui import Ui_GenerateGameWidget
from randovania.gui.lib import async_dialog
from randovania.gui.lib.generation_failure_handling import GenerationFailureHandler
from randovania.interface_common import generator_frontend
from randovania.layout.generator_parameters import GeneratorParameters
from randovania.layout.permalink import Permalink
from randovania.resolver.exceptions import ImpossibleForSolver

if TYPE_CHECKING:
    from pathlib import Path

    from randovania.games.game import RandovaniaGame
    from randovania.gui.lib.background_task_mixin import BackgroundTaskMixin
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.options import Options
    from randovania.layout.layout_description import LayoutDescription
    from randovania.layout.versioned_preset import VersionedPreset
    from randovania.lib.status_update_lib import ProgressUpdateCallable


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


class GenerateGameWidget(QtWidgets.QWidget, Ui_GenerateGameWidget):
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

        self.num_players_spin_box.setVisible(self._window_manager.is_preview_mode)
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

    @asyncSlot()
    async def generate_new_layout_regular(self) -> None:
        monitoring.metrics.incr("gui_generate_plain")
        return await self.generate_new_layout(spoiler=True)

    @asyncSlot()
    async def generate_new_layout_no_retry(self) -> None:
        monitoring.metrics.incr("gui_generate_no_retry")
        return await self.generate_new_layout(spoiler=True, retries=0)

    @asyncSlot()
    async def generate_new_layout_race(self) -> None:
        monitoring.metrics.incr("gui_generate_race")
        return await self.generate_new_layout(spoiler=False)

    async def generate_new_layout(self, spoiler: bool, retries: int | None = None) -> None:
        preset = self.preset
        num_players = self.num_players_spin_box.value()

        unsupported_features = preset.get_preset().configuration.unsupported_features()
        if unsupported_features:
            if randovania.is_dev_version():
                confirmation = "Are you sure you want to continue?"
                buttons = async_dialog.StandardButton.Yes | async_dialog.StandardButton.No
            else:
                confirmation = "These features are not available outside of development builds."
                buttons = async_dialog.StandardButton.No

            result = await async_dialog.warning(
                self,
                "Unsupported Features",
                "Preset '{}' uses the unsupported features:\n{}\n\n{}".format(
                    preset.name,
                    ", ".join(unsupported_features),
                    confirmation,
                ),
                buttons=buttons,
                default_button=async_dialog.StandardButton.No,
            )
            if result != async_dialog.StandardButton.Yes:
                return

        while True:
            try:
                return await self.generate_layout_from_permalink(
                    permalink=Permalink.from_parameters(
                        GeneratorParameters(
                            seed_number=random.randint(0, 2**31),
                            spoiler=spoiler,
                            presets=[preset.get_preset()] * num_players,
                        )
                    ),
                    retries=retries,
                )
            except RetryGeneration:
                pass

    async def generate_layout_from_permalink(self, permalink: Permalink, retries: int | None = None) -> None:
        def work(progress_update: ProgressUpdateCallable) -> LayoutDescription:
            return generator_frontend.generate_layout(
                progress_update=progress_update, parameters=permalink.parameters, options=self._options, retries=retries
            )

        if self._window_manager.is_preview_mode:
            logging.info(f"Permalink: {permalink.as_base64_str}")

        try:
            layout = await self._background_task.run_in_background_async(work, "Creating a game...")
        except ImpossibleForSolver as e:
            code = await async_dialog.warning(
                self,
                "Solver Error",
                f"{e}.\n\nDo you want to:"
                f"\n- Keep the generated game, even without any guarantees it's possible"
                f"\n- Retry the generation"
                f"\n- Cancel the process",
                buttons=(
                    async_dialog.StandardButton.Save
                    | async_dialog.StandardButton.Retry
                    | async_dialog.StandardButton.Cancel
                ),
                default_button=async_dialog.StandardButton.Cancel,
            )
            if code == async_dialog.StandardButton.Save:
                layout = e.layout
            elif code == async_dialog.StandardButton.Retry:
                raise RetryGeneration
            else:
                self._background_task.progress_update_signal.emit("Solver Error", 0)
                return

        except asyncio.exceptions.CancelledError:
            return

        except Exception as e:
            return await self.failure_handler.handle_exception(e, self._background_task.progress_update_signal.emit)

        self._background_task.progress_update_signal.emit(f"Success! (Seed hash: {layout.shareable_hash})", 100)
        persist_layout(self._options.game_history_path, layout)
        self._window_manager.open_game_details(layout)

    def on_options_changed(self, options: Options) -> None:
        self.select_preset_widget.on_options_changed(options)

    def _on_can_generate(self, can_generate: bool) -> None:
        for btn in [
            self.create_generate_button,
            self.create_generate_race_button,
            self.create_generate_no_retry_button,
        ]:
            btn.setEnabled(can_generate)
