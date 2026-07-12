from PySide6.QtCore import QModelIndex, QObject, Signal
from PySide6.QtWidgets import QAbstractItemView, QTreeView, QWidget

from .model import RequirementModel


class RequirementView(QObject):
    selection_changed = Signal(QModelIndex)

    def __init__(self, parent: QWidget, tree: QTreeView, model: RequirementModel) -> None:
        super().__init__(parent)

        tree.setModel(model)
        tree.expandAll()

        tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        tree.clicked.connect(self._notify_selection_changed)

        self._tree = tree

    def _on_model_rebuilt(self) -> None:
        self._tree.expandAll()

    def _notify_selection_changed(self, index: QModelIndex) -> None:
        self.selection_changed.emit(index)

    def deleteLater(self) -> None:
        self._tree.deleteLater()
