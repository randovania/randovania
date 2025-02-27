from __future__ import annotations

import typing

from PySide6 import QtCore, QtWidgets

if typing.TYPE_CHECKING:
    from pathlib import Path

    from randovania.game.game_enum import RandovaniaGame
    from randovania.gui.lib.qt_network_client import QtNetworkClient
    from randovania.gui.multiworld_client import MultiworldClient
    from randovania.interface_common.options import Options
    from randovania.interface_common.preset_manager import PresetManager
    from randovania.layout.base.trick_level_configuration import TrickLevelConfiguration
    from randovania.layout.layout_description import LayoutDescription
    from randovania.layout.preset import Preset
    from randovania.layout.versioned_preset import VersionedPreset


class WidgetWithClose(typing.Protocol):
    CloseEvent = QtCore.Signal()


class WindowManager(QtWidgets.QMainWindow):
    tracked_windows: list[WidgetWithClose]

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

    def track_window(self, window: WidgetWithClose) -> None:
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

    def import_preset_file(self, path: Path) -> VersionedPreset | None:
        """
        Imports a preset file.
        :param path:
        :return: The preset if it was actually imported, None otherwise.
        """
        raise NotImplementedError
