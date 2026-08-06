from typing import cast

from PySide6.QtCore import QItemSelectionModel, QModelIndex, QObject, QPersistentModelIndex, QSize, Qt, Signal
from PySide6.QtGui import QAbstractTextDocumentLayout, QPainter, QPalette, QTextDocument
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTreeView,
    QWidget,
)

from randovania.game_description.requirements.array_base import RequirementArrayBase

from .model import ROLE, RequirementModel
from .path import RequirementTreePath


class RequirementView(QObject):
    selection_changed = Signal(QModelIndex)

    def __init__(self, parent: QWidget, tree: QTreeView, model: RequirementModel) -> None:
        super().__init__(parent)

        tree.setModel(model)
        tree.setItemDelegate(RequirementDelegate(tree))
        tree.expandAll()

        tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        tree.selectionModel().currentChanged.connect(self._notify_selection_changed)

        self._tree = tree

    def _on_model_rebuilt(self) -> None:
        self._tree.expandAll()

    def _notify_selection_changed(self, current: QModelIndex, previous: QModelIndex) -> None:
        self.selection_changed.emit(current)

    def restore_selection(self, path: RequirementTreePath) -> None:
        model = cast(RequirementModel, self._tree.model())
        index = model.index_from_path(path)

        selection_model = self._tree.selectionModel()
        selection_model.setCurrentIndex(index, QItemSelectionModel.SelectionFlag.ClearAndSelect)

        self._tree.setFocus()
        self._tree.scrollTo(index, QAbstractItemView.ScrollHint.EnsureVisible)


class RequirementDelegate(QStyledItemDelegate):
    """Renders Array comments in bold green"""

    def _build_document(
        self, option: QStyleOptionViewItem, index: QModelIndex | QPersistentModelIndex
    ) -> QTextDocument | None:
        requirement = index.data(ROLE)
        if not isinstance(requirement, RequirementArrayBase) or requirement.comment is None:
            return None

        text: str = index.data(Qt.ItemDataRole.DisplayRole)
        array_type, _, comment = text.partition("\n")

        # Resolve text color for array type
        # Without this, text color defaults to black with no regard for light/dark mode or selection state
        color_group = (
            QPalette.ColorGroup.Normal
            if option.state & QStyle.StateFlag.State_Enabled
            else QPalette.ColorGroup.Disabled
        )
        color_role = (
            QPalette.ColorRole.HighlightedText
            if option.state & QStyle.StateFlag.State_Selected
            else QPalette.ColorRole.Text
        )
        text_color = option.palette.color(color_group, color_role)

        html: str = (
            f"<span style='color:{text_color.name()}'>{array_type}</span>"
            f"<br><span style='font-weight: bold; color:green'>{comment}</span>"
        )

        document = QTextDocument()
        document.setHtml(html)
        document.setDefaultFont(option.font)
        document.setTextWidth(option.rect.width())

        return document

    def paint(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex | QPersistentModelIndex
    ) -> None:
        document = self._build_document(option, index)
        if document is None:
            super().paint(painter, option, index)
            return

        _option = QStyleOptionViewItem(option)
        self.initStyleOption(_option, index)
        _option.text = ""

        style: QStyle = _option.widget.style() if _option.widget else QApplication.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, _option, painter, _option.widget)

        painter.save()
        text_rect = style.subElementRect(QStyle.SubElement.SE_ItemViewItemText, _option, _option.widget)
        painter.translate(text_rect.topLeft())
        document.documentLayout().draw(painter, QAbstractTextDocumentLayout.PaintContext())
        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex | QPersistentModelIndex) -> QSize:
        document = self._build_document(option, index)
        if document is None:
            return super().sizeHint(option, index)
        return document.size().toSize()
