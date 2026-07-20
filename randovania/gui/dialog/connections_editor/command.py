from PySide6.QtGui import QUndoCommand

from randovania.game_description.requirements.base import Requirement

from .model import RequirementModel
from .path import Path
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
        before_selection_path: Path,
        after_selection_path: Path,
        description: str,
    ) -> None:
        super().__init__(description)
        self._model = model
        self._view = view
        self._before = before
        self._after = after
        self._before_selection_path = before_selection_path
        self._after_selection_path = after_selection_path

    def redo(self) -> None:
        self._model.build_tree(self._after)
        self._view.restore_selection(self._after_selection_path)

    def undo(self) -> None:
        self._model.build_tree(self._before)
        self._view.restore_selection(self._before_selection_path)
