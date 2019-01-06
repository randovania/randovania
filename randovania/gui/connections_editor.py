from typing import Optional

from PySide2.QtWidgets import QDialog, QWidget

from randovania.game_description.requirements import RequirementSet
from randovania.game_description.resources import ResourceDatabase
from randovania.gui.common_qt_lib import set_default_window_icon
from randovania.gui.connections_editor_ui import Ui_ConnectionEditor
from randovania.gui.connections_visualizer import ConnectionsVisualizer


class ConnectionsEditor(QDialog, Ui_ConnectionEditor):
    def __init__(self, parent: QWidget, resource_database: ResourceDatabase, requirement_set: Optional[RequirementSet]):
        super().__init__(parent)
        self.setupUi(self)
        set_default_window_icon(self)

        self._connections_visualizer = ConnectionsVisualizer(
            self.visualizer_contents,
            self.gridLayout,
            resource_database,
            requirement_set,
            True,
            num_columns_for_alternatives=1
        )
        self.new_alternative_button.clicked.connect(self._connections_visualizer.new_alternative)

    @property
    def final_requirement_set(self) -> Optional[RequirementSet]:
        result = self._connections_visualizer.build_requirement_set()
        if result == RequirementSet.impossible():
            return None
        return result
