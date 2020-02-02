from typing import Optional

from PySide2.QtWidgets import QWidget

from randovania.layout.layout_configuration import LayoutConfiguration


class WindowManager(QWidget):
    def open_map_tracker(self, configuration: LayoutConfiguration):
        raise NotImplemented()

    def open_data_visualizer_at(self, world_name: Optional[str], area_name: Optional[str]):
        raise NotImplemented()
