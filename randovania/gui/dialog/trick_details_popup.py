import re
from typing import Optional

from PySide2.QtWidgets import QDialog, QWidget

from randovania.game_description.area import Area
from randovania.game_description.game_description import GameDescription
from randovania.game_description.node import DockNode
from randovania.game_description.requirements import RequirementList, Requirement
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.trick_resource_info import TrickResourceInfo
from randovania.gui.generated.trick_details_popup_ui import Ui_TrickDetailsPopup
from randovania.gui.lib.common_qt_lib import set_default_window_icon
from randovania.gui.lib.window_manager import WindowManager
from randovania.layout.trick_level import LayoutTrickLevel


def _has_trick(alternative: RequirementList) -> bool:
    return any(individual.resource.resource_type == ResourceType.TRICK for individual in alternative.values())


def _area_uses_trick(area: Area,
                     trick: TrickResourceInfo,
                     level: LayoutTrickLevel,
                     ) -> bool:
    """
    Checks the area RequirementSet in the given Area uses the given trick at the given level.
    :param area:
    :param trick:
    :param level:
    :return:
    """

    def _uses_trick(requirements: Requirement) -> bool:
        return any(individual.resource == trick and individual.amount == level.as_number
                   for individual in requirements.as_set.all_individual)

    for node in area.nodes:
        if isinstance(node, DockNode):
            if _uses_trick(node.default_dock_weakness.requirement):
                return True

        if any(_uses_trick(req) for req in area.connections[node].values()):
            return True

    return False


class TrickDetailsPopup(QDialog, Ui_TrickDetailsPopup):
    def __init__(self,
                 parent: QWidget,
                 window_manager: WindowManager,
                 game_description: GameDescription,
                 trick: TrickResourceInfo,
                 level: LayoutTrickLevel,
                 ):
        super().__init__(parent)
        self.setupUi(self)
        set_default_window_icon(self)

        self._window_manager = window_manager
        self._game_description = game_description

        # setup
        self.setWindowTitle(f"Trick Details: {trick.long_name} at {level.long_name}")
        self.title_label.setText(self.title_label.text().format(
            trick=trick,
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
            lines = [
                f'<a href="data-editor://{world.correct_name(area.in_dark_aether)}/{area.name}">{world.correct_name(area.in_dark_aether)} - {area.name}</a>'
                for (world, area) in areas_to_show
            ]
            self.area_list_label.setText("<br />".join(sorted(lines)))

        else:
            self.area_list_label.setText("This trick is not used in this level.")

    def button_box_close(self):
        self.reject()

    def _on_click_link_to_data_editor(self, link: str):
        info = re.match(r"^data-editor://([^)]+)/([^)]+)$", link)
        if info:
            world_name, area_name = info.group(1, 2)
            self._window_manager.open_data_visualizer_at(world_name, area_name, game=self._game_description.game)
