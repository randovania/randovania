from __future__ import annotations

import asyncio
import random
from typing import TYPE_CHECKING

import randovania
from randovania.gui.lib import async_dialog
from randovania.gui.lib.common_qt_lib import alert_user_on_generation
from randovania.interface_common import generator_frontend
from randovania.layout.generator_parameters import GeneratorParameters
from randovania.layout.permalink import Permalink
from randovania.resolver.exceptions import ImpossibleForSolver

if TYPE_CHECKING:
    from PySide6 import QtWidgets

    from randovania.gui.lib.background_task_mixin import BackgroundTaskMixin
    from randovania.gui.lib.generation_failure_handling import GenerationFailureHandler
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.options import Options
    from randovania.layout.layout_description import LayoutDescription
    from randovania.layout.versioned_preset import VersionedPreset
    from randovania.lib.status_update_lib import ProgressUpdateCallable


class RetryGeneration(Exception):
    pass


class GenerateGameMixin:
    _background_task: BackgroundTaskMixin
    _window_manager: WindowManager
    _options: Options
    failure_handler: GenerationFailureHandler

    @property
    def preset(self) -> VersionedPreset:
        raise NotImplementedError

    @property
    def num_worlds(self) -> int:
        return 1

    @property
    def generate_parent_widget(self) -> QtWidgets.QWidget:
        raise NotImplementedError

    async def generate_new_layout(self, spoiler: bool, retries: int | None = None) -> LayoutDescription | None:
        """

        :param spoiler:
        :param retries:
        :return:
        """
        preset = self.preset
        num_players = self.num_worlds

        unsupported_features = preset.get_preset().configuration.unsupported_features()
        if unsupported_features:
            if randovania.is_dev_version():
                confirmation = "Are you sure you want to continue?"
                buttons = async_dialog.StandardButton.Yes | async_dialog.StandardButton.No
            else:
                confirmation = "These features are not available outside of development builds."
                buttons = async_dialog.StandardButton.No

            result = await async_dialog.warning(
                self.generate_parent_widget,
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
                return None

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

    async def generate_layout_from_permalink(
        self, permalink: Permalink, retries: int | None = None
    ) -> LayoutDescription | None:
        """

        :param permalink:
        :param retries:
        :return:
        """

        def work(progress_update: ProgressUpdateCallable) -> LayoutDescription:
            return generator_frontend.generate_layout(
                progress_update=progress_update, parameters=permalink.parameters, options=self._options, retries=retries
            )

        try:
            layout = await self._background_task.run_in_background_async(work, "Creating a game...")
        except ImpossibleForSolver as e:
            code = await async_dialog.warning(
                self.generate_parent_widget,
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
            alert_user_on_generation(self.generate_parent_widget, self._options)
            if code == async_dialog.StandardButton.Save:
                layout = e.layout
            elif code == async_dialog.StandardButton.Retry:
                raise RetryGeneration
            else:
                self._background_task.progress_update_signal.emit("Solver Error", 0)
                return None

        except asyncio.exceptions.CancelledError:
            return None

        except Exception as e:
            alert_user_on_generation(self.generate_parent_widget, self._options)
            await self.failure_handler.handle_exception(e, self._background_task.progress_update_signal.emit)
            return None

        self._background_task.progress_update_signal.emit(f"Success! (Seed hash: {layout.shareable_hash})", 100)
        alert_user_on_generation(self.generate_parent_widget, self._options)
        return layout
