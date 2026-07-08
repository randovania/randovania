from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any, cast

from PySide6.QtCore import (
    QItemSelectionModel,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    Qt,
    Signal,
)
from PySide6.QtGui import QKeySequence, QStandardItem, QStandardItemModel, QUndoCommand, QUndoStack
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLayout,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QStackedWidget,
    QTreeView,
    QWidget,
)

from randovania.game_description.db.area import Area
from randovania.game_description.db.node import Node
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.db.region import Region
from randovania.game_description.db.region_list import RegionList
from randovania.game_description.requirements.array_base import RequirementArrayBase
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.node_requirement import NodeRequirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_or import RequirementOr
from randovania.game_description.requirements.requirement_template import RequirementTemplate
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.resource_database import NamedRequirementTemplate, ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceInfo
from randovania.game_description.resources.resource_type import ResourceType
from randovania.gui.generated.connections_editor_ui import Ui_ConnectionEditor
from randovania.gui.lib.common_qt_lib import set_default_window_icon
from randovania.gui.lib.signal_handling import set_combo_with_value
from randovania.gui.widgets.scroll_protected import ScrollProtectedComboBox
from randovania.layout.base.trick_level import LayoutTrickLevel
from randovania.lib.enum_lib import iterate_enum


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


_ROLE = Qt.ItemDataRole.UserRole


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
        index: QModelIndex = self._model._index_from_path(self._selection_path)
        self._view._tree.selectionModel().select(index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        self._view._tree.setFocus()
        self._view._notify_selection_changed(index)

    def undo(self) -> None:
        self._model.build_tree(self._before)


class RequirementModel(QStandardItemModel):
    model_rebuilt = Signal()

    def __init__(self) -> None:
        super().__init__()

    def _requirement_to_str(self, requirement: Requirement) -> str:
        if isinstance(requirement, RequirementArrayBase):
            text = "All" if isinstance(requirement, RequirementAnd) else "Any"
            if len(requirement.items) == 0:
                text += " (Empty)"
            if requirement.comment is not None:
                text += f"\n{requirement.comment}"
            return text

        if isinstance(requirement, ResourceRequirement):
            if requirement.resource.resource_type == ResourceType.TRICK:
                return (
                    f"{requirement.resource.long_name} ({LayoutTrickLevel.from_number(requirement.amount).long_name})"
                )
            return requirement.pretty_text

        if isinstance(requirement, RequirementTemplate):
            return str(requirement)

        if isinstance(requirement, NodeRequirement):
            return requirement.node_identifier.as_string

        raise RuntimeError(f"Unknown requirement type: {type(requirement)} - {requirement}")

    def _item_from_requirement(self, requirement: Requirement) -> QStandardItem:
        item = QStandardItem(self._requirement_to_str(requirement))
        item.setData(requirement, _ROLE)
        return item

    def _path_from_index(self, index: QModelIndex) -> list[int]:
        path = []
        while index.isValid():
            path.append(index.row())
            index = index.parent()
        path.reverse()
        return path

    def _index_from_path(self, path: list[int]) -> QModelIndex:
        index = QModelIndex()
        for row in path:
            next_index = self.index(row, 0, index)
            if not next_index.isValid():
                return index  # Fallback to deepest valid ancenstor
            index = next_index
        return index

    def build_tree(self, requirement: Requirement) -> None:
        """
        Populates the model with the given Requirement
        """

        def walk(_requirement: Requirement, parent: QStandardItem) -> None:
            item = self._item_from_requirement(_requirement)
            if isinstance(_requirement, RequirementArrayBase):
                for inner_requirement in _requirement.items:
                    walk(inner_requirement, item)
            parent.appendRow(item)

        self.clear()
        self.setColumnCount(1)
        self.setHorizontalHeaderLabels(["Requirement"])
        walk(requirement, self.invisibleRootItem())
        self.model_rebuilt.emit()

    def build_requirement(self) -> Requirement:
        """
        Constructs a requirement from the current model state
        """

        def walk(item: QStandardItem) -> Requirement:
            requirement: Requirement = item.data(_ROLE)

            if isinstance(requirement, RequirementArrayBase):
                children = [walk(item.child(idx)) for idx in range(item.rowCount())]
                return type(requirement)(children, requirement.comment)

            return requirement

        return walk(self.invisibleRootItem().child(0))

    def flags(self, index: QModelIndex | QPersistentModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

        # if index.parent().isValid():
        #    flags |= Qt.ItemFlag.ItemIsDragEnabled

        # requirement = self.itemFromIndex(index).data(_ROLE)
        # if isinstance(requirement, RequirementArrayBase):
        #    flags |= Qt.ItemFlag.ItemIsDropEnabled

        return flags


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


class RequirementController(QObject):
    requirement_changed = Signal(QModelIndex, Requirement)

    def __init__(
        self,
        parent: QWidget,
        stacked_widget: QStackedWidget,
        combo_requirement_type: QComboBox,
        db: ResourceDatabase,
        region_list: RegionList,
        model: RequirementModel,
        view: RequirementView,
        undo_stack: QUndoStack,
    ) -> None:
        super().__init__(parent)

        self._stacked_widget = stacked_widget
        self._combo_type = combo_requirement_type
        self._db = db
        self._region_list = region_list
        self._view = view
        self._model = model
        self._undo_stack = undo_stack

        self._editors: dict[ResourceType | type[Requirement], Editor] = {}
        self._active_item_index: QModelIndex | None = None

        self._build_editors()

        self._combo_type.currentIndexChanged.connect(self._on_type_combo_changed)

    def _build_editors(self) -> None:
        editors: list[Editor] = [
            CountedResourceEditor(self._db, self._stacked_widget, "Item", ResourceType.ITEM),
            SimpleResourceEditor(self._db, self._stacked_widget, "Event", ResourceType.EVENT),
            TrickResourceEditor(self._db, self._stacked_widget),
            CountedResourceEditor(self._db, self._stacked_widget, "Damage", ResourceType.DAMAGE),
            SimpleResourceEditor(self._db, self._stacked_widget, "Version", ResourceType.VERSION),
            SimpleResourceEditor(self._db, self._stacked_widget, "Misc", ResourceType.MISC),
            TemplateEditor(self._db, self._stacked_widget),
            NodeEditor(self._db, self._stacked_widget, self._region_list),
            ArrayEditor(self._db, self._stacked_widget),
        ]

        for editor in editors:
            self._editors[editor.type()] = editor
            self._stacked_widget.addWidget(editor.widget())

            self._combo_type.addItem(editor.name(), editor.type())

            editor.changed.connect(self._on_editor_field_changed)

    def _insert_requirement_item(
        self, items: tuple[Requirement, ...], item: Requirement, idx: int
    ) -> tuple[Requirement, ...]:
        return (*items[:idx], item, *items[idx:])

    def _replace_requirement_item(
        self, items: tuple[Requirement, ...], item: Requirement, idx: int
    ) -> tuple[Requirement, ...]:
        return (*items[:idx], item, *items[idx + 1 :])

    def _insert_at_path(
        self, root: RequirementArrayBase, path: list[int], at_idx: int, requirement: Requirement
    ) -> Requirement:
        """
        Returns a new Requirement tree with the Requirement inserted
        """
        if len(path) == 0:
            new_items = self._insert_requirement_item(root.items, requirement, at_idx)
            return type(root)(new_items, root.comment)

        idx = path[0]
        next_root = root.items[idx]
        assert isinstance(next_root, RequirementArrayBase)
        child = self._insert_at_path(next_root, path[1:], at_idx, requirement)
        new_items = self._replace_requirement_item(root.items, child, idx)
        return type(root)(new_items, root.comment)

    def _remove_at_path(self, root: RequirementArrayBase, path: list[int]) -> Requirement:
        """
        Returns a new Requirement tree with the Requirement at `path` removed
        """
        idx = path[0]

        if len(path) == 1:
            new_items = (*root.items[:idx], *root.items[idx + 1 :])
            return type(root)(new_items, root.comment)

        next_root = root.items[idx]
        assert isinstance(next_root, RequirementArrayBase)
        child = self._remove_at_path(next_root, path[1:])
        new_items = self._replace_requirement_item(root.items, child, idx)
        return type(root)(new_items, root.comment)

    def _replace_at_path(self, root: RequirementArrayBase, path: list[int], requirement: Requirement) -> Requirement:
        """
        Returns a new Requirement tree with the Requirement at `path` replaced
        """
        if len(path) == 0:
            return requirement

        idx = path[0]
        next_root = root.items[idx]
        child = (
            self._replace_at_path(next_root, path[1:], requirement)
            if isinstance(next_root, RequirementArrayBase)
            else requirement
        )
        new_items = self._replace_requirement_item(root.items, child, idx)
        return type(root)(new_items, root.comment)

    def _default_requirement_for_type(self, _type: type) -> Requirement:
        if isinstance(_type, ResourceType):
            resource_info: ResourceInfo = self._db.get_by_type(_type)[0]
            return ResourceRequirement.simple(resource_info)

        if issubclass(_type, RequirementArrayBase):
            return RequirementAnd([], None)

        if _type == RequirementTemplate:
            template_name = next(iter(self._db.requirement_template))
            return RequirementTemplate(template_name)

        if _type == NodeRequirement:
            node: Node = next(self._region_list.iterate_nodes())
            return NodeRequirement(node.identifier)

        raise RuntimeError(f"Unknown requirement type: {_type}")

    def _change_requirement_type(self, current: Requirement, to_type: type) -> Requirement:
        # Array -> Array
        if isinstance(current, RequirementArrayBase) and issubclass(type(to_type), RequirementArrayBase):
            return to_type(current.items, current.comment)

        return self._default_requirement_for_type(to_type)

    def _show_editor(self, editor: Editor) -> None:
        self._stacked_widget.setCurrentWidget(editor.widget())

    def _get_editor_for(self, requirement: Requirement) -> Editor | None:
        if requirement is None:
            return None

        if isinstance(requirement, ResourceRequirement):
            return self._editors[requirement.resource.resource_type]
        elif isinstance(requirement, RequirementArrayBase):
            return self._editors[RequirementArrayBase]
        else:
            return self._editors[type(requirement)]

    def _on_item_selected(self, index: QModelIndex) -> None:
        """
        Switch to the editor for the selected Requirement type and update fields
        """
        self._active_item_index = index
        requirement: Requirement = index.data(_ROLE)
        editor: Editor | None = self._get_editor_for(requirement)
        type_idx: int = -1

        if editor is not None:
            editor.populate(requirement)
            self._show_editor(editor)
            type_idx = self._combo_type.findData(editor.type(), _ROLE)

        with signals_blocked(self._combo_type):
            self._combo_type.setCurrentIndex(type_idx)

    def _on_add_requirement_pressed(self) -> None:
        if self._active_item_index is None:
            return

        before: Requirement = self._model.build_requirement()

        # Root is not array type, can't add requirement
        if not self._active_item_index.parent().isValid() and not isinstance(before, RequirementArrayBase):
            return

        assert isinstance(before, RequirementArrayBase)
        path: list[int] = self._model._path_from_index(self._active_item_index)
        requirement_path = path[1:]
        row: int = path[-1]
        selected = self._active_item_index.data(_ROLE)

        new_type = self._combo_type.currentData(_ROLE)
        requirement: Requirement = self._default_requirement_for_type(new_type)

        if isinstance(selected, RequirementArrayBase):
            # Array, add as child
            row = len(selected.items)
        elif self._active_item_index.parent().isValid():
            # Leaf, add as sibling
            requirement_path.pop()
            row += 1
        else:
            # Root is leaf, can't add sibling
            return

        after: Requirement = self._insert_at_path(before, requirement_path, row, requirement)
        selection_path: list[int] = path[:1] + requirement_path + [row]

        self._undo_stack.push(Command(self._model, self._view, before, after, selection_path, "Add Requirement"))

    def _on_delete_requirement_pressed(self) -> None:
        if self._active_item_index is None:
            return

        # Can't delete root
        if not self._active_item_index.parent().isValid():
            return

        before: Requirement = self._model.build_requirement()
        assert isinstance(before, RequirementArrayBase)
        path: list[int] = self._model._path_from_index(self._active_item_index)
        row: int = path[-1]
        after: Requirement = self._remove_at_path(before, path[1:])

        # Determine path for re-selection
        selection_path: list[int] = list(path)
        sibling_count: int = self._model.itemFromIndex(self._active_item_index).parent().rowCount()

        if sibling_count == 1:
            # No siblings remain, select parent
            selection_path.pop()
        elif row == sibling_count - 1:
            # Was last child, select previous sibling
            selection_path[-1] = row - 1

        self._undo_stack.push(Command(self._model, self._view, before, after, selection_path, "Delete Requirement"))

    def _on_shift_up_pressed(self) -> None:
        if self._active_item_index is None:
            return

        # Can't shift root
        if not self._active_item_index.parent().isValid():
            return

        path: list[int] = self._model._path_from_index(self._active_item_index)
        requirement_path = path[1:]
        row: int = path[-1]

        selected: Requirement = self._active_item_index.data(_ROLE)
        before: Requirement = self._model.build_requirement()
        assert isinstance(before, RequirementArrayBase)
        after_remove: Requirement = self._remove_at_path(before, requirement_path)
        assert isinstance(after_remove, RequirementArrayBase)

        if row > 0:
            # Next sibling exists
            row -= 1
            sibling_path: list[int] = [*path[:-1], row]
            sibling_requirement = self._model._index_from_path(sibling_path).data(_ROLE)
            if isinstance(sibling_requirement, RequirementArrayBase):
                # Sibling is an array, ascend into
                row = len(sibling_requirement.items)
                requirement_path = [*sibling_path[1:], row]
        elif len(requirement_path) > 1:
            # Escape parent
            requirement_path.pop()
            row = requirement_path[-1]
        else:
            # Already at top, can't shift up
            return

        after: Requirement = self._insert_at_path(after_remove, requirement_path[:-1], row, selected)
        selection_path: list[int] = path[:1] + requirement_path[:-1] + [row]

        self._undo_stack.push(Command(self._model, self._view, before, after, selection_path, "Move up"))

    def _on_shift_down_pressed(self) -> None:
        if self._active_item_index is None:
            return

        # Can't shift root
        if not self._active_item_index.parent().isValid():
            return

        path: list[int] = self._model._path_from_index(self._active_item_index)
        requirement_path = path[1:]
        row: int = path[-1]
        rows: int = self._model.itemFromIndex(self._active_item_index).parent().rowCount()

        selected: Requirement = self._active_item_index.data(_ROLE)
        before: Requirement = self._model.build_requirement()
        assert isinstance(before, RequirementArrayBase)
        after_remove: Requirement = self._remove_at_path(before, requirement_path)
        assert isinstance(after_remove, RequirementArrayBase)

        if row < rows - 1:
            # Next sibling exists
            row += 1
            sibling_path: list[int] = [*path[:-1], row]
            if isinstance(self._model._index_from_path(sibling_path).data(_ROLE), RequirementArrayBase):
                # Sibling is an array, descend into
                row = 0
                requirement_path.extend([row])
        elif len(requirement_path) > 1:
            # Escape parent
            requirement_path.pop()
            row = requirement_path[-1] + 1
        else:
            # Already at bottom, can't shift down
            return

        after: Requirement = self._insert_at_path(after_remove, requirement_path[:-1], row, selected)
        selection_path: list[int] = path[:1] + requirement_path[:-1] + [row]

        self._undo_stack.push(Command(self._model, self._view, before, after, selection_path, "Move down"))

    def _on_type_combo_changed(self, idx: int = -1) -> None:
        if self._active_item_index is None:
            return

        before: Requirement = self._model.build_requirement()

        current: Requirement = self._active_item_index.data(_ROLE)
        new_type: type = self._combo_type.currentData(_ROLE)
        changed: Requirement = self._change_requirement_type(current, new_type)

        path: list[int] = self._model._path_from_index(self._active_item_index)
        after: Requirement = (
            self._replace_at_path(before, path[1:], changed) if isinstance(before, RequirementArrayBase) else changed
        )

        self._undo_stack.push(Command(self._model, self._view, before, after, path, "Change Type"))

    def _on_editor_field_changed(self, requirement: Requirement) -> None:
        if self._active_item_index is None:
            return

        current: Requirement = self._active_item_index.data(_ROLE)
        if isinstance(requirement, RequirementArrayBase) and isinstance(current, RequirementArrayBase):
            requirement.items = current.items

        before: Requirement = self._model.build_requirement()
        path: list[int] = self._model._path_from_index(self._active_item_index)
        after: Requirement = (
            self._replace_at_path(before, path[1:], requirement)
            if isinstance(before, RequirementArrayBase)
            else requirement
        )

        self._undo_stack.push(Command(self._model, self._view, before, after, path, "Requirement edit"))

    def deleteLater(self) -> None:
        self._stacked_widget.deleteLater()
        self._combo_type.deleteLater()


class Editor(QObject):
    _db: ResourceDatabase
    _widget: QWidget
    _display_name: str
    _type: ResourceType | type[Requirement]

    changed = Signal(Requirement)

    def __init__(
        self, db: ResourceDatabase, parent: QWidget, display_name: str, type: ResourceType | type[Requirement]
    ) -> None:
        super().__init__()
        self._db = db
        self._create_base(parent)
        self._display_name = display_name
        self._type = type

    def populate(self, requirement: Requirement) -> None:
        """
        Populate editor widgets with requirement data without emitting signals
        """
        raise NotImplementedError

    def requirement(self) -> Requirement:
        """
        Assemble a new requirement with current widget selections
        """
        raise NotImplementedError

    def widget(self) -> QWidget:
        return self._widget

    def name(self) -> str:
        return self._display_name

    def type(self) -> ResourceType | type[Requirement]:
        return self._type

    def _create_base(self, parent: QWidget) -> None:
        self._widget = QWidget(parent)
        layout = QHBoxLayout(self._widget)
        self._widget.setLayout(layout)

    def _create_combo_with_data(
        self, data: list[Any], to_string: Callable[[Any], str] = str
    ) -> ScrollProtectedComboBox:
        """
        Creates a QComboBox and attaches data <br>
        Optionally accepts a custom Callable to convert the data to string, defaulting to str()
        """
        combo = ScrollProtectedComboBox(self._widget)
        combo.setEditable(False)
        for resource in data:
            combo.addItem(to_string(resource), resource)
        return combo

    def _create_boolean_combo(self) -> ScrollProtectedComboBox:
        return self._create_combo_with_data([False, True], lambda b: "<" if b else "≥")

    def _create_spin_box(self, min: int, max: int) -> QSpinBox:
        spin_box = QSpinBox(self._widget)
        spin_box.setMinimum(min)
        spin_box.setMaximum(max)
        return spin_box

    def _create_check_box(self) -> QCheckBox:
        return QCheckBox(self._widget)

    def _create_line_edit(self, placeholder: str = "") -> QLineEdit:
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        return line_edit

    def _add_to_layout(self, widgets: list[QWidget]) -> None:
        layout: QLayout | None = self._widget.layout()
        assert layout is not None
        for widget in widgets:
            layout.addWidget(widget)

    def _notify_changed(self, *args: Any) -> None:
        self.changed.emit(self.requirement())


class ResourceEditor(Editor):
    _resource_type: ResourceType

    def __init__(self, db: ResourceDatabase, parent: QWidget, display_name: str, resource_type: ResourceType) -> None:
        super().__init__(db, parent, display_name, ResourceRequirement)
        self._resource_type = resource_type

        resources = self._db.get_by_type(self._resource_type)
        self._combo_name = self._create_combo_with_data(resources, self.to_string)

        self._combo_name.currentIndexChanged.connect(self._notify_changed)

        self._add_to_layout([self._combo_name])

    def type(self) -> ResourceType:
        return self._resource_type

    def to_string(self, resource_info: ResourceInfo) -> str:
        return resource_info.long_name

    def populate(self, requirement: Requirement) -> None:
        requirement = cast(ResourceRequirement, requirement)
        with signals_blocked(self._combo_name):
            self._set_name_combo(requirement.resource)

    def _set_name_combo(self, resource_info: ResourceInfo) -> None:
        set_combo_with_value(self._combo_name, resource_info)

    def _make_requirement(self, amount: int, negate: bool) -> ResourceRequirement:
        resource_info: ResourceInfo = self._combo_name.currentData(_ROLE)
        return ResourceRequirement.create(resource_info, amount, negate)

    def requirement(self) -> Requirement:
        raise NotImplementedError


class CountedResourceEditor(ResourceEditor):
    """
    Editor for resources with varying amounts: Item, Damage
    """

    def __init__(self, db: ResourceDatabase, parent: QWidget, display_name: str, resource_type: ResourceType) -> None:
        super().__init__(db, parent, display_name, resource_type)

        self._combo_negate = self._create_boolean_combo()
        self._spinbox_amount = self._create_spin_box(1, 1)

        self._combo_negate.currentIndexChanged.connect(self._notify_changed)
        self._spinbox_amount.valueChanged.connect(self._notify_changed)

        self._add_to_layout([self._combo_negate, self._spinbox_amount])

    def populate(self, requirement: Requirement) -> None:
        super().populate(requirement)
        requirement = cast(ResourceRequirement, requirement)
        with signals_blocked(self._combo_negate):
            self._set_negate_combo(requirement.negate)
        with signals_blocked(self._spinbox_amount):
            self._set_spinbox(requirement)

    def _set_negate_combo(self, value: bool) -> None:
        set_combo_with_value(self._combo_negate, value)

    def _set_spinbox(self, requirement: ResourceRequirement) -> None:
        resource_info: ResourceInfo = requirement.resource
        max: int = 10_000  # NOTE - Arbitrary value for damage

        if isinstance(resource_info, ItemResourceInfo):
            max = resource_info.max_capacity

        self._spinbox_amount.setMaximum(max)
        self._spinbox_amount.setValue(requirement.amount)

    def requirement(self) -> ResourceRequirement:
        return self._make_requirement(self._spinbox_amount.value(), self._combo_negate.currentData(_ROLE))


class TrickResourceEditor(ResourceEditor):
    def __init__(self, db: ResourceDatabase, parent: QWidget) -> None:
        super().__init__(db, parent, "Trick", ResourceType.TRICK)

        difficulties = list(iterate_enum(LayoutTrickLevel))[1:]  # Discard LayoutTrickLevel.DISABLED
        self._combo_difficulty = self._create_combo_with_data(difficulties, lambda level: level.long_name)

        self._combo_difficulty.currentIndexChanged.connect(self._notify_changed)

        self._add_to_layout([self._combo_difficulty])

    def populate(self, requirement: Requirement) -> None:
        super().populate(requirement)
        requirement = cast(ResourceRequirement, requirement)
        with signals_blocked(self._combo_difficulty):
            self._set_difficulty_combo(requirement.amount)

    def _set_difficulty_combo(self, value: int) -> None:
        set_combo_with_value(self._combo_difficulty, LayoutTrickLevel.from_number(value))

    def requirement(self) -> ResourceRequirement:
        return self._make_requirement(self._combo_difficulty.currentData(_ROLE).as_number, False)


class SimpleResourceEditor(ResourceEditor):
    """
    Editor for resources with an unchanging amount (1): Event, Version, Misc
    """

    def __init__(self, db: ResourceDatabase, parent: QWidget, display_name: str, resource_type: ResourceType) -> None:
        super().__init__(db, parent, display_name, resource_type)

        self._checkbox_negate = self._create_check_box()

        self._checkbox_negate.checkStateChanged.connect(self._notify_changed)

        self._add_to_layout([self._checkbox_negate])

    def populate(self, requirement: Requirement) -> None:
        super().populate(requirement)
        requirement = cast(ResourceRequirement, requirement)
        with signals_blocked(self._checkbox_negate):
            self._set_negate_combo(requirement)

    def _set_negate_combo(self, requirement: ResourceRequirement) -> None:
        self._checkbox_negate.setChecked(requirement.negate)

        if requirement.resource.resource_type == ResourceType.EVENT:
            self._checkbox_negate.setText(
                ResourceType.EVENT.negated_prefix if requirement.negate else ResourceType.EVENT.non_negated_prefix
            )

    def requirement(self) -> ResourceRequirement:
        return self._make_requirement(1, self._checkbox_negate.isChecked())


class TemplateEditor(Editor):
    def __init__(self, db: ResourceDatabase, parent: QWidget) -> None:
        super().__init__(db, parent, "Template", RequirementTemplate)

        templates = list(self._db.requirement_template.values())
        self._combo_name = self._create_combo_with_data(templates, self.to_string)

        self._combo_name.currentIndexChanged.connect(self._notify_changed)

        self._add_to_layout([self._combo_name])

    def to_string(self, template: NamedRequirementTemplate) -> str:
        return template.display_name

    def populate(self, requirement: Requirement) -> None:
        requirement = cast(RequirementTemplate, requirement)
        with signals_blocked(self._combo_name):
            self._set_name_combo(requirement.template_name)

    def _set_name_combo(self, template_name: str) -> None:
        template: NamedRequirementTemplate = self._db.requirement_template[template_name]
        set_combo_with_value(self._combo_name, template)

    def requirement(self) -> RequirementTemplate:
        name: str = self.to_string(self._combo_name.currentData(_ROLE))
        return RequirementTemplate(name)


class NodeEditor(Editor):
    def __init__(self, db: ResourceDatabase, parent: QWidget, region_list: RegionList) -> None:
        super().__init__(db, parent, "Node", NodeRequirement)
        self._region_list = region_list

        self._combo_region = self._create_combo_with_data(self._region_list.regions, self.to_string)
        self._combo_area = self._create_combo_with_data([])
        self._combo_node = self._create_combo_with_data([])

        self._add_to_layout([self._combo_region, self._combo_area, self._combo_node])

        self._combo_region.currentIndexChanged.connect(self._region_changed)
        self._combo_area.currentIndexChanged.connect(self._area_changed)
        self._combo_node.currentIndexChanged.connect(self._notify_changed)

    def to_string(self, data: Region | Area | Node) -> str:
        return data.name

    def _repopulate_combo(self, combo: QComboBox, data: list[Any]) -> None:
        combo.clear()
        for item in data:
            combo.addItem(self.to_string(item), item)

    def populate(self, requirement: Requirement) -> None:
        requirement = cast(NodeRequirement, requirement)
        region: Region = self._region_list.region_with_name(requirement.node_identifier.region)
        with signals_blocked(self._combo_region):
            set_combo_with_value(self._combo_region, region)
        with signals_blocked(self._combo_node):
            self._region_changed(requirement=requirement)

    def _region_changed(self, idx: int = -1, requirement: NodeRequirement | None = None) -> None:
        region: Region = self._combo_region.currentData(_ROLE)
        with signals_blocked(self._combo_area):
            self._repopulate_combo(self._combo_area, region.areas)

        if requirement is not None:
            area: Area = region.area_by_identifier(requirement.node_identifier.area_identifier)
            with signals_blocked(self._combo_area):
                set_combo_with_value(self._combo_area, area)

        self._area_changed(requirement=requirement)

    def _area_changed(self, idx: int = -1, requirement: NodeRequirement | None = None) -> None:
        area: Area = self._combo_area.currentData(_ROLE)
        with signals_blocked(self._combo_node):
            self._repopulate_combo(self._combo_node, area.nodes)

        if requirement is not None:
            node: Node = self._region_list.node_by_identifier(requirement.node_identifier)
            with signals_blocked(self._combo_node):
                set_combo_with_value(self._combo_node, node)

    def requirement(self) -> NodeRequirement:
        node_identifier = NodeIdentifier(
            self.to_string(self._combo_region.currentData(_ROLE)),
            self.to_string(self._combo_area.currentData(_ROLE)),
            self.to_string(self._combo_node.currentData(_ROLE)),
        )
        return NodeRequirement(node_identifier)


class ArrayEditor(Editor):
    def __init__(self, db: ResourceDatabase, parent: QWidget) -> None:
        super().__init__(db, parent, "Array", RequirementArrayBase)

        self._combo_type = self._create_combo_with_data([RequirementAnd, RequirementOr], self.to_string)
        self._line_edit_comment = self._create_line_edit("Comment")

        self._combo_type.currentIndexChanged.connect(self._notify_changed)
        self._line_edit_comment.editingFinished.connect(self._notify_changed)

        self._add_to_layout([self._combo_type, self._line_edit_comment])

    def to_string(self, _type: type[RequirementAnd] | type[RequirementOr]) -> str:
        return _type.combinator().strip().title()

    def populate(self, requirement: Requirement) -> None:
        requirement = cast(RequirementArrayBase, requirement)
        with signals_blocked(self._combo_type):
            self._set_type_combo(requirement)
        with signals_blocked(self._line_edit_comment):
            self._set_comment_line_edit(requirement.comment)

    def _set_type_combo(self, requirement: RequirementArrayBase) -> None:
        set_combo_with_value(self._combo_type, type(requirement))

    def _set_comment_line_edit(self, text: str | None) -> None:
        if text is None:
            self._line_edit_comment.clear()
            return
        self._line_edit_comment.setText(text)

    def requirement(self) -> RequirementArrayBase:
        _type: type = self._combo_type.currentData(_ROLE)
        text: str = self._line_edit_comment.text()
        comment: str | None = text if len(text) > 0 else None
        return _type([], comment)


@contextmanager
def signals_blocked(widget: QWidget) -> Iterator[None]:
    previous = widget.signalsBlocked()
    widget.blockSignals(True)
    yield
    widget.blockSignals(previous)
