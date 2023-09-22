from __future__ import annotations

import typing

from PySide6 import QtWidgets

if typing.TYPE_CHECKING:
    from randovania.games.game import RandovaniaGame
    from randovania.gui.lib.close_event_widget import CloseEventWidget
    from randovania.gui.lib.qt_network_client import QtNetworkClient
    from randovania.gui.multiworld_client import MultiworldClient
    from randovania.interface_common.options import Options
    from randovania.interface_common.preset_manager import PresetManager
    from randovania.layout.base.trick_level_configuration import TrickLevelConfiguration
    from randovania.layout.layout_description import LayoutDescription
    from randovania.layout.preset import Preset


class WindowManager(QtWidgets.QMainWindow):
    tracked_windows: list[CloseEventWidget]

    def __init__(self):
        super().__init__()
        self.tracked_windows = []

    @property
    def preset_manager(self) -> PresetManager:
        raise NotImplementedError

    @property
    def multiworld_client(self) -> MultiworldClient:
        raise NotImplementedError

    async def open_map_tracker(self, configuration: Preset):
        raise NotImplementedError

    def open_data_visualizer_at(
        self,
        region_name: str | None,
        area_name: str | None,
        game: RandovaniaGame,
        trick_levels: TrickLevelConfiguration | None = None,
    ):
        raise NotImplementedError

    def open_game_details(self, layout: LayoutDescription, players: list[str] | None = None):
        raise NotImplementedError

    def open_game_connection_window(self):
        raise NotImplementedError

    def set_games_selector_visible(self, visible: bool):
        raise NotImplementedError

    @property
    def main_window(self) -> QtWidgets.QMainWindow:
        raise NotImplementedError

    @property
    def is_preview_mode(self) -> bool:
        raise NotImplementedError

    def track_window(self, window: CloseEventWidget):
        def remove_window():
            self.tracked_windows.remove(window)

        window.CloseEvent.connect(remove_window)
        self.tracked_windows.append(window)

    async def ensure_multiplayer_session_window(
        self, network_client: QtNetworkClient, session_id: int, options: Options
    ):
        raise NotImplementedError

    def open_app_navigation_link(self, link: str):
        raise NotImplementedError
