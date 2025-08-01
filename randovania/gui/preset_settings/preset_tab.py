from __future__ import annotations

import dataclasses
import typing

from PySide6 import QtWidgets

from randovania.layout.base.base_configuration import BaseConfiguration

if typing.TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetTab[BaseConfigurationT: BaseConfiguration](QtWidgets.QMainWindow):
    RANDOMIZER_LOGIC_HEADER = "Randomizer Logic"
    GAME_MODIFICATIONS_HEADER = "Game Modifications"

    def __init__(
        self, editor: PresetEditor[BaseConfigurationT], game_description: GameDescription, window_manager: WindowManager
    ):
        super().__init__()
        self._editor = editor
        self.game_description = game_description
        self._window_manager = window_manager

    def update_experimental_visibility(self) -> None:
        show_experimental = self._editor._options.experimental_settings
        show_development = show_experimental and self._window_manager.is_preview_mode

        for w in self.experimental_settings:
            w.setVisible(show_experimental)
        for w in self.development_settings:
            w.setVisible(show_development)

    @classmethod
    def is_experimental(cls) -> bool:
        return False

    @property
    def experimental_settings(self) -> typing.Iterable[QtWidgets.QWidget]:
        """Widgets to be hidden unless experimental settings are enabled."""
        yield from []

    @property
    def development_settings(self) -> typing.Iterable[QtWidgets.QWidget]:
        """
        Widgets to be hidden unless experimental settings are enabled
        and RDV is running in preview mode.
        """
        yield from []

    @classmethod
    def tab_title(cls) -> str:
        raise NotImplementedError

    @classmethod
    def header_name(cls) -> str | None:
        """If this tab starts a new header, returns the name of the header. If it doesn't, returns None."""
        raise NotImplementedError

    def on_preset_changed(self, preset: Preset[BaseConfigurationT]) -> None:
        raise NotImplementedError

    # Persistence helpers
    def _persist_enum(self, combo: QtWidgets.QComboBox, attribute_name: str):
        def persist(index: int):
            with self._editor as options:
                options.set_configuration_field(attribute_name, combo.itemData(index))

        return persist

    def _persist_bool_layout_field(self, field_name: str):
        def bound(value: int):
            with self._editor as editor:
                editor.set_configuration_field(field_name, bool(value))

        return bound

    def _persist_bool_major_configuration_field(self, field_name: str):
        def bound(value: int):
            with self._editor as editor:
                kwargs = {field_name: bool(value)}
                editor.standard_pickup_configuration = dataclasses.replace(
                    editor.standard_pickup_configuration,
                    **kwargs,
                )

        return bound

    def _persist_option_then_notify(self, attribute_name: str):
        def persist(value: int):
            with self._editor as options:
                options.set_configuration_field(attribute_name, bool(value))

        return persist

    def _persist_argument(self, attribute_name: str):
        def persist(value: float):
            with self._editor as options:
                options.set_configuration_field(attribute_name, value)

        return persist
