from typing import Optional, List

from PySide2.QtWidgets import QWidget, QMainWindow

from randovania.games.game import RandovaniaGame
from randovania.gui.lib.close_event_widget import CloseEventWidget
from randovania.interface_common.preset_manager import PresetManager
from randovania.layout.echoes_configuration import EchoesConfiguration
from randovania.layout.layout_description import LayoutDescription


class WindowManager(QMainWindow):
    tracked_windows: List[CloseEventWidget]

    def __init__(self):
        super().__init__()
        self.tracked_windows = []

    @property
    def preset_manager(self) -> PresetManager:
        raise NotImplemented()

    def open_map_tracker(self, configuration: EchoesConfiguration):
        raise NotImplemented()

    def open_data_visualizer_at(self, world_name: Optional[str], area_name: Optional[str],
                                game: RandovaniaGame = RandovaniaGame.PRIME2):
        raise NotImplemented()

    def open_game_details(self, layout: LayoutDescription):
        raise NotImplemented()

    @property
    def main_window(self) -> QMainWindow:
        raise NotImplemented()

    @property
    def is_preview_mode(self) -> bool:
        raise NotImplemented()

    def track_window(self, window: CloseEventWidget):
        def remove_window():
            self.tracked_windows.remove(window)

        window.CloseEvent.connect(remove_window)
        self.tracked_windows.append(window)
