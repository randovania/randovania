from __future__ import annotations

from PySide6.QtGui import QKeySequence, QUndoStack
from PySide6.QtWidgets import QDialog, QMessageBox, QWidget

from randovania.game_description.db.region_list import RegionList
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.gui.generated.connections_editor_ui import Ui_ConnectionEditor
from randovania.gui.lib.common_qt_lib import set_default_window_icon

from .controller import RequirementController
from .model import RequirementModel
from .view import RequirementView


class ConnectionsEditor(QDialog, Ui_ConnectionEditor):
    def __init__(
        self,
        parent: QWidget,
        resource_database: ResourceDatabase,
        region_list: RegionList,
        requirement: Requirement,
    ) -> None:
        super().__init__(parent)
        self.setupUi(self)
        set_default_window_icon(self)

        self._undo_stack = QUndoStack(self)

        undo_action = self._undo_stack.createUndoAction(self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        redo_action = self._undo_stack.createRedoAction(self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)

        self.addAction(undo_action)
        self.addAction(redo_action)

        self._model = RequirementModel()
        self._view = RequirementView(parent, self.tree_view, self._model)
        self._controller = RequirementController(
            parent,
            self.stacked_widget,
            self.combo_requirement_type,
            resource_database,
            region_list,
            self._model,
            self._view,
            self._undo_stack,
        )

        # Connect Signals
        self._model.model_rebuilt.connect(self._view._on_model_rebuilt)
        self._view.selection_changed.connect(self._controller._on_item_selected)

        self.button_add_requirement.clicked.connect(self._controller._on_add_requirement_pressed)
        self.button_delete.clicked.connect(self._controller._on_delete_requirement_pressed)
        self.button_shift_up.clicked.connect(self._controller._on_shift_up_pressed)
        self.button_shift_down.clicked.connect(self._controller._on_shift_down_pressed)
        self.button_undo.clicked.connect(self._undo_stack.undo)
        self.button_redo.clicked.connect(self._undo_stack.redo)

        # Don't push command for initial build so it can't be undone
        self._model.build_tree(requirement)

    def deleteLater(self) -> None:
        self._controller.deleteLater()
        self._view.deleteLater()
        self._model.deleteLater()

    @property
    def final_requirement(self) -> Requirement:
        result = self._model.build_requirement()
        assert result is not None
        return result

    def accept(self) -> None:
        result = self._model.build_requirement()
        if result is None:
            QMessageBox.critical(self, "Invalid Configuration", "Unable to confirm selection, invalid values found.")
        else:
            super().accept()
