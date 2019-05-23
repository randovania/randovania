import re

from PySide2.QtWidgets import QDialog

from randovania.game_description.area import Area
from randovania.game_description.game_description import GameDescription
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.gui.common_qt_lib import set_default_window_icon
from randovania.gui.main_window import MainWindow
from randovania.gui.trick_details_popup_ui import Ui_TrickDetailsPopup
from randovania.layout.trick_level import LayoutTrickLevel

_INVALID_MODELS = {
    0, 1, 9, 10, 16,
}


def _area_uses_trick(area: Area,
                     trick: SimpleResourceInfo,
                     level: LayoutTrickLevel,
                     ) -> bool:
    """
    Checks the area RequirementSet in the given Area uses the given trick at the given level.
    :param area:
    :param trick:
    :param level:
    :return:
    """
    for _, _, requirements in area.all_connections:
        for individual in requirements.all_individual:
            if individual.resource == trick and individual.amount == level.as_number:
                return True
    return False


class TrickDetailsPopup(QDialog, Ui_TrickDetailsPopup):
    def __init__(self,
                 parent: MainWindow,
                 game_description: GameDescription,
                 trick: SimpleResourceInfo,
                 level: LayoutTrickLevel,
                 ):
        super().__init__(parent)
        self.setupUi(self)
        set_default_window_icon(self)

        self._trick = trick
        self._level = level
        self._main_window = parent

        # setup
        self.setWindowTitle(f"Trick Details: {trick.long_name} at {level.long_name}")
        self.title_label.setText(self.title_label.text().format(
            trick=trick.long_name,
            level=level.long_name,
        ))
        self.area_list_label.linkActivated.connect(self._on_click_link_to_data_editor)

        # connect
        self.button_box.accepted.connect(self.button_box_close)
        self.button_box.rejected.connect(self.button_box_close)

        # Update
        areas_to_show = [
            (world, area)
            for world in game_description.world_list.worlds
            for area in world.areas
            if _area_uses_trick(area, trick, level)
        ]

        if areas_to_show:
            self.area_list_label.setText("<br />".join(
                f'<a href="data-editor://{world.name}/{area.name}">{world.name} - {area.name}</a>'
                for (world, area) in areas_to_show
            ))

        else:
            self.area_list_label.setText("This trick is not used in this level.")

    def button_box_close(self):
        self.reject()

    def _on_click_link_to_data_editor(self, link: str):
        info = re.match(r"^data-editor://([^)]+)/([^)]+)$", link)
        if info:
            world_name, area_name = info.group(1, 2)
            self._main_window.open_data_visualizer_at(world_name, area_name)
