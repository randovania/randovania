from __future__ import annotations

import re
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QDialog, QWidget

from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.node import NodeContext
from randovania.game_description.resources.resource_collection import ResourceCollection
from randovania.gui.generated.trick_details_popup_ui import Ui_TrickDetailsPopup
from randovania.gui.lib.common_qt_lib import set_default_window_icon

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from randovania.game_description.db.area import Area
    from randovania.game_description.db.region import Region
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.requirements.base import Requirement
    from randovania.game_description.requirements.resource_requirement import ResourceRequirement
    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.game_description.resources.trick_resource_info import TrickResourceInfo
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.layout.base.trick_level import LayoutTrickLevel
    from randovania.layout.base.trick_level_configuration import TrickLevelConfiguration


def _requirement_at_value(resource: ResourceInfo, level: LayoutTrickLevel):
    def criteria(individual: ResourceRequirement):
        return individual.resource == resource and individual.amount == level.as_number

    return criteria


def _area_uses_resource(
    area: Area,
    criteria: Callable[[ResourceRequirement], bool],
    context: NodeContext,
) -> Iterable[str]:
    """
    Checks the area RequirementSet in the given Area uses the given trick at the given level.
    :param area:
    :param resource:
    :param level:
    :return:
    """

    def _uses_trick(requirements: Requirement) -> bool:
        return any(criteria(individual) for individual in requirements.iterate_resource_requirements(context))

    def _dock_uses_trick(dock: DockNode):
        if _uses_trick(dock.default_dock_weakness.requirement):
            return True

        if dock.default_dock_weakness.lock is not None:
            if _uses_trick(dock.default_dock_weakness.lock.requirement):
                return True

        if dock.override_default_open_requirement is not None:
            if _uses_trick(dock.override_default_open_requirement):
                return True

        if dock.override_default_lock_requirement is not None:
            if _uses_trick(dock.override_default_lock_requirement):
                return True

        return False

    for node in area.nodes:
        if isinstance(node, DockNode):
            if _dock_uses_trick(node):
                yield f"Open {node.name}"

        for target, req in area.connections[node].items():
            if _uses_trick(req):
                yield f"{node.name} -> {target.name}"


class BaseResourceDetailsPopup(QDialog, Ui_TrickDetailsPopup):
    def __init__(
        self,
        parent: QWidget,
        window_manager: WindowManager,
        game_description: GameDescription,
        areas_to_show: list[tuple[Region, Area, list[str]]],
        trick_levels: TrickLevelConfiguration | None = None,
    ):
        super().__init__(parent)
        self.setupUi(self)
        set_default_window_icon(self)

        self._window_manager = window_manager
        self._game_description = game_description
        self._trick_levels = trick_levels

        # setup
        self.area_list_label.linkActivated.connect(self._on_click_link_to_data_editor)

        # connect
        self.button_box.accepted.connect(self.button_box_close)
        self.button_box.rejected.connect(self.button_box_close)

        # Update
        if areas_to_show:
            lines = [
                (
                    f'<a href="data-editor://{region.correct_name(area.in_dark_aether)}/{area.name}">'
                    f"{region.correct_name(area.in_dark_aether)} - {area.name}</a>"
                )
                + "".join(f"\n<br />{usage}" for usage in usages)
                + "<br />"
                for (region, area, usages) in areas_to_show
            ]
            self.area_list_label.setText("<br />".join(sorted(lines)))
        else:
            self.area_list_label.setText("This trick is not used in this level.")

    def button_box_close(self):
        self.reject()

    def _on_click_link_to_data_editor(self, link: str):
        info = re.match(r"^data-editor://([^)]+)/([^)]+)$", link)
        if info:
            region_name, area_name = info.group(1, 2)
            self._window_manager.open_data_visualizer_at(
                region_name,
                area_name,
                game=self._game_description.game,
                trick_levels=self._trick_levels,
            )


class TrickDetailsPopup(BaseResourceDetailsPopup):
    def __init__(
        self,
        parent: QWidget,
        window_manager: WindowManager,
        game_description: GameDescription,
        trick: TrickResourceInfo,
        level: LayoutTrickLevel,
        trick_levels: TrickLevelConfiguration | None = None,
    ):
        context = NodeContext(
            None, ResourceCollection(), game_description.resource_database, game_description.region_list
        )
        areas_to_show = [
            (region, area, usages)
            for region in game_description.region_list.regions
            for area in region.areas
            if (usages := list(_area_uses_resource(area, _requirement_at_value(trick, level), context)))
        ]
        super().__init__(parent, window_manager, game_description, areas_to_show, trick_levels)

        # setup
        self.setWindowTitle(f"Trick Details: {trick.long_name} at {level.long_name}")
        self.title_label.setText(
            self.title_label.text().format(
                trick=trick,
                level=level.long_name,
            )
        )


class ResourceDetailsPopup(BaseResourceDetailsPopup):
    def __init__(
        self,
        parent: QWidget,
        window_manager: WindowManager,
        game_description: GameDescription,
        resource: ResourceInfo,
    ):
        def is_resource(individual: ResourceRequirement):
            return individual.resource == resource

        context = NodeContext(
            None, ResourceCollection(), game_description.resource_database, game_description.region_list
        )
        areas_to_show = [
            (region, area, usages)
            for region in game_description.region_list.regions
            for area in region.areas
            if (usages := list(_area_uses_resource(area, is_resource, context)))
        ]
        super().__init__(parent, window_manager, game_description, areas_to_show)

        # setup
        self.setWindowTitle(f"Details for {resource.long_name}")
        self.title_label.setText(
            f"""<html><head/><body>
        <p><span style=" font-weight:600;">{resource.long_name}</span></p>
        <p>{resource.long_name} can be found in the rooms listed below.</p>
        <p>Click a room name to open it in the Data Visualizer for more details.</p>
        </body></html>"""
        )
