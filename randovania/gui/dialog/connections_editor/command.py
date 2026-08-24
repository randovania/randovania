from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QUndoCommand

if TYPE_CHECKING:
    from randovania.game_description.requirements.base import Requirement
    from randovania.gui.dialog.connections_editor.model import RequirementModel
    from randovania.gui.dialog.connections_editor.path import RequirementTreePath
    from randovania.gui.dialog.connections_editor.view import RequirementView


class RequirementEditCommand(QUndoCommand):
    """
    A reversible edit to a requirement tree.

    Stores a snapshot of the tree and the selection path both before and after the edit.
    """

    def __init__(
        self,
        model: RequirementModel,
        view: RequirementView,
        before: Requirement,
        after: Requirement,
        before_selection_path: RequirementTreePath,
        after_selection_path: RequirementTreePath,
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
