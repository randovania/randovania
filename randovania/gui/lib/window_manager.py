from typing import Optional

from PySide2.QtWidgets import QWidget, QMainWindow

from randovania.interface_common.preset_manager import PresetManager
from randovania.layout.layout_configuration import LayoutConfiguration
from randovania.layout.layout_description import LayoutDescription


class WindowManager(QWidget):
    @property
    def preset_manager(self) -> PresetManager:
        raise NotImplemented()

    def open_map_tracker(self, configuration: LayoutConfiguration):
        raise NotImplemented()

    def open_data_visualizer_at(self, world_name: Optional[str], area_name: Optional[str]):
        raise NotImplemented()

    def show_seed_tab(self, layout: LayoutDescription):
        raise NotImplemented()

    @property
    def main_window(self) -> QMainWindow:
        raise NotImplemented()

    @property
    def is_preview_mode(self) -> bool:
        raise NotImplemented()
