from PySide6.QtCore import QItemSelectionModel, QModelIndex
from PySide6.QtGui import QUndoCommand

from randovania.game_description.requirements.base import Requirement

from .model import RequirementModel
from .view import RequirementView


class Command(QUndoCommand):
    """
    Captures tree state to allow for undo/redo
    """

    def __init__(
        self,
        model: RequirementModel,
        view: RequirementView,
        before: Requirement,
        after: Requirement,
        selection_path: list[int],
        description: str,
    ) -> None:
        super().__init__(description)
        self._model = model
        self._view = view
        self._before = before
        self._after = after
        self._selection_path = selection_path

    def redo(self) -> None:
        self._model.build_tree(self._after)
        index: QModelIndex = self._model.index_from_path(self._selection_path)
        self._view._tree.selectionModel().select(index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        self._view._tree.setFocus()
        self._view._notify_selection_changed(index)

    def undo(self) -> None:
        self._model.build_tree(self._before)
