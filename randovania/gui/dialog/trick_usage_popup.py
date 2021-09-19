import re
from typing import Iterator, Dict

from PySide2 import QtWidgets
from PySide2.QtWidgets import QWidget

from randovania.game_description import default_database
from randovania.game_description.requirements import RequirementSet, ResourceRequirement
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import CurrentResources
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.trick_resource_info import TrickResourceInfo
from randovania.game_description.world.area import Area
from randovania.game_description.world.node import DockNode
from randovania.gui.generated.trick_usage_popup_ui import Ui_TrickUsagePopup
from randovania.gui.lib.common_qt_lib import set_default_window_icon
from randovania.gui.lib.window_manager import WindowManager
from randovania.layout.base.trick_level import LayoutTrickLevel
from randovania.layout.base.trick_level_configuration import TrickLevelConfiguration
from randovania.layout.preset import Preset
from randovania.resolver import bootstrap


def _area_requirement_sets(area: Area,
                           database: ResourceDatabase,
                           ) -> Iterator[RequirementSet]:
    """
    Checks the area RequirementSet in the given Area uses the given trick at the given level.
    :param area:
    :param database:
    :return:
    """

    for node in area.nodes:
        if isinstance(node, DockNode):
            yield node.default_dock_weakness.requirement.as_set(database)

        for req in area.connections[node].values():
            yield req.as_set(database)


def _check_used_tricks(area: Area, trick_resources: CurrentResources, database: ResourceDatabase):
    result = set()

    for s in _area_requirement_sets(area, database):
        for alternative in s.alternatives:
            tricks: Dict[TrickResourceInfo, ResourceRequirement] = {
                req.resource: req
                for req in alternative.items
                if req.resource.resource_type == ResourceType.TRICK
            }
            if tricks and all(trick_resources[trick] >= tricks[trick].amount for trick in tricks):
                line = [
                    f"{trick.long_name} ({LayoutTrickLevel.from_number(req.amount).long_name})"
                    for trick, req in tricks.items()
                ]
                result.add(" and ".join(sorted(line)))

    return sorted(result)


class TrickUsagePopup(QtWidgets.QDialog, Ui_TrickUsagePopup):
    def __init__(self,
                 parent: QWidget,
                 window_manager: WindowManager,
                 preset: Preset,
                 ):

        super().__init__(parent)
        self.setupUi(self)
        set_default_window_icon(self)

        self._window_manager = window_manager
        self._game_description = default_database.game_description_for(preset.game)
        database = self._game_description.resource_database

        trick_level = preset.configuration.trick_level
        if trick_level.minimal_logic:
            trick_usage_description = "Minimal Logic"
        else:
            trick_usage_description = ", ".join(sorted(
                f"{trick.long_name} ({trick_level.level_for_trick(trick).long_name})"
                for trick in database.trick
                if trick_level.has_specific_level_for_trick(trick)
            ))

        # setup
        self.area_list_label.linkActivated.connect(self._on_click_link_to_data_editor)
        self.setWindowTitle("{} for preset {}".format(self.windowTitle(), preset.name))
        self.title_label.setText(self.title_label.text().format(
            trick_levels=trick_usage_description
        ))

        # connect
        self.button_box.accepted.connect(self.button_box_close)
        self.button_box.rejected.connect(self.button_box_close)

        if trick_level.minimal_logic:
            return

        # Update
        trick_resources = bootstrap.trick_resources_for_configuration(trick_level, database)

        lines = []

        for world in sorted(self._game_description.world_list.worlds, key=lambda it: it.name):
            for area in sorted(world.areas, key=lambda it: it.name):
                used_tricks = _check_used_tricks(area, trick_resources, database)
                if used_tricks:
                    lines.append(
                        f'<p><a href="data-editor://{world.correct_name(area.in_dark_aether)}/{area.name}">'
                        f'{world.correct_name(area.in_dark_aether)} - {area.name}</a>'
                        f'<br />{"<br />".join(used_tricks)}</p>'
                    )

        self.area_list_label.setText("".join(lines))

    def button_box_close(self):
        self.reject()

    def _on_click_link_to_data_editor(self, link: str):
        info = re.match(r"^data-editor://([^)]+)/([^)]+)$", link)
        if info:
            world_name, area_name = info.group(1, 2)
            self._window_manager.open_data_visualizer_at(world_name, area_name, game=self._game_description.game)
