from __future__ import annotations

import typing

from PySide6.QtWidgets import QMainWindow


if typing.TYPE_CHECKING:
    from randovania.games.game import RandovaniaGame
    from randovania.gui.lib.close_event_widget import CloseEventWidget
    from randovania.interface_common.preset_manager import PresetManager
    from randovania.layout.layout_description import LayoutDescription
    from randovania.layout.preset import Preset
    from randovania.layout.base.trick_level_configuration import TrickLevelConfiguration


class WindowManager(QMainWindow):
    tracked_windows: list[CloseEventWidget]

    def __init__(self):
        super().__init__()
        self.tracked_windows = []

    @property
    def preset_manager(self) -> PresetManager:
        raise NotImplementedError()

    async def open_map_tracker(self, configuration: Preset):
        raise NotImplementedError()

    def open_data_visualizer_at(self, world_name: str | None, area_name: str | None, game: RandovaniaGame,
                                trick_levels: TrickLevelConfiguration | None = None):
        raise NotImplementedError()

    def open_game_details(self, layout: LayoutDescription):
        raise NotImplementedError()

    def set_games_selector_visible(self, visible: bool):
        raise NotImplementedError()

    @property
    def main_window(self) -> QMainWindow:
        raise NotImplementedError()

    @property
    def is_preview_mode(self) -> bool:
        raise NotImplementedError()

    def track_window(self, window: CloseEventWidget):
        def remove_window():
            self.tracked_windows.remove(window)

        window.CloseEvent.connect(remove_window)
        self.tracked_windows.append(window)
