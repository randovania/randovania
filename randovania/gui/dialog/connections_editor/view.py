from typing import cast

from PySide6.QtCore import QItemSelectionModel, QModelIndex, QObject, Signal
from PySide6.QtWidgets import QAbstractItemView, QTreeView, QWidget

from .model import RequirementModel
from .path import Path


class RequirementView(QObject):
    selection_changed = Signal(QModelIndex)

    def __init__(self, parent: QWidget, tree: QTreeView, model: RequirementModel) -> None:
        super().__init__(parent)

        tree.setModel(model)
        tree.expandAll()

        tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        tree.selectionModel().currentChanged.connect(self._notify_selection_changed)

        self._tree = tree

    def _on_model_rebuilt(self) -> None:
        self._tree.expandAll()

    def _notify_selection_changed(self, current: QModelIndex, previous: QModelIndex) -> None:
        self.selection_changed.emit(current)

    def restore_selection(self, path: Path) -> None:
        model = cast(RequirementModel, self._tree.model())
        index = model.index_from_path(path)

        selection_model = self._tree.selectionModel()
        selection_model.setCurrentIndex(index, QItemSelectionModel.SelectionFlag.ClearAndSelect)

        self._tree.setFocus()
        self._tree.scrollTo(index, QAbstractItemView.ScrollHint.EnsureVisible)
