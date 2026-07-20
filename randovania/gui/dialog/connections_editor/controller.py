from typing import Any

from PySide6.QtCore import QModelIndex, QObject, Signal
from PySide6.QtGui import QUndoStack
from PySide6.QtWidgets import QComboBox, QStackedWidget, QWidget

from randovania.game_description.db.node import Node
from randovania.game_description.db.region_list import RegionList
from randovania.game_description.requirements.array_base import RequirementArrayBase
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.node_requirement import NodeRequirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_template import RequirementTemplate
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceInfo
from randovania.game_description.resources.resource_type import ResourceType

from .command import Command
from .editor import (
    ArrayEditor,
    CountedResourceEditor,
    Editor,
    NodeEditor,
    SimpleResourceEditor,
    TemplateEditor,
    TrickResourceEditor,
    signals_blocked,
)
from .model import ROLE, RequirementModel
from .path import Path
from .view import RequirementView


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
        self._active_item_index: QModelIndex

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

    def _tuple_insert(self, items: tuple, idx: int, value: Any) -> tuple:
        return (*items[:idx], value, *items[idx:])

    def _tuple_replace(self, items: tuple, idx: int, value: Any) -> tuple:
        return (*items[:idx], value, *items[idx + 1 :])

    def _tuple_remove(self, items: tuple, idx: int) -> tuple:
        return (*items[:idx], *items[idx + 1 :])

    def _insert_at_path(self, root: RequirementArrayBase, path: Path, requirement: Requirement) -> Requirement:
        """
        Returns a new Requirement tree with the Requirement inserted
        """
        if len(path) == 1:
            new_items = self._tuple_insert(root.items, path.row(), requirement)
            return type(root)(new_items, root.comment)

        idx = path.head()
        next_root = root.items[idx]
        assert isinstance(next_root, RequirementArrayBase)
        child = self._insert_at_path(next_root, path.tail(), requirement)
        new_items = self._tuple_replace(root.items, idx, child)
        return type(root)(new_items, root.comment)

    def _remove_at_path(self, root: RequirementArrayBase, path: Path) -> Requirement:
        """
        Returns a new Requirement tree with the Requirement at `path` removed
        """
        idx = path.head()

        if len(path) == 1:
            new_items = self._tuple_remove(root.items, idx)
            return type(root)(new_items, root.comment)

        next_root = root.items[idx]
        assert isinstance(next_root, RequirementArrayBase)
        child = self._remove_at_path(next_root, path.tail())
        new_items = self._tuple_replace(root.items, idx, child)
        return type(root)(new_items, root.comment)

    def _replace_at_path(self, root: RequirementArrayBase, path: Path, requirement: Requirement) -> Requirement:
        """
        Returns a new Requirement tree with the Requirement at `path` replaced
        """
        if len(path) == 0:
            return requirement

        idx = path.head()
        next_root = root.items[idx]
        child = (
            self._replace_at_path(next_root, path.tail(), requirement)
            if isinstance(next_root, RequirementArrayBase)
            else requirement
        )
        new_items = self._tuple_replace(root.items, idx, child)
        return type(root)(new_items, root.comment)

    def _default_requirement_for_type(self, _type: ResourceType | type[Requirement]) -> Requirement:
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
        """Wrapper to retain requirement data when changing between array types"""
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
        requirement: Requirement = index.data(ROLE)
        editor: Editor | None = self._get_editor_for(requirement)
        type_idx: int = -1

        if editor is not None:
            editor.populate(requirement)
            self._show_editor(editor)
            type_idx = self._combo_type.findData(editor.type(), ROLE)

        with signals_blocked(self._combo_type):
            self._combo_type.setCurrentIndex(type_idx)

    def _active_is_root(self) -> bool:
        return not self._active_item_index.parent().isValid()

    def _active_is_array(self) -> bool:
        return isinstance(self._active_item_index.data(ROLE), RequirementArrayBase)

    def _push_command(
        self, before: Requirement, after: Requirement, after_selection_path: Path, description: str
    ) -> None:
        before_selection_path = self._model.path_from_index(self._active_item_index)
        self._undo_stack.push(
            Command(self._model, self._view, before, after, before_selection_path, after_selection_path, description)
        )

    def _on_add_requirement_pressed(self) -> None:
        active = self._active_item_index.data(ROLE)
        path = self._model.path_from_index(self._active_item_index)

        if self._active_is_array():
            path = path.extend_with(len(active.items))
        elif len(path) > 0:
            # Leaf is selected and is not the root
            path = path.next_sibling()
        else:
            return

        before: Requirement = self._model.build_requirement()
        assert isinstance(before, RequirementArrayBase)
        new_requirement: Requirement = self._default_requirement_for_type(self._combo_type.currentData(ROLE))
        after: Requirement = self._insert_at_path(before, path, new_requirement)

        self._push_command(before, after, path, "Add Requirement")

    def _on_delete_requirement_pressed(self) -> None:
        # Can't delete root
        if self._active_is_root():
            return

        before: Requirement = self._model.build_requirement()
        assert isinstance(before, RequirementArrayBase)
        path = self._model.path_from_index(self._active_item_index)
        after: Requirement = self._remove_at_path(before, path)

        sibling_count: int = self._model.sibling_count(path)

        if sibling_count == 0:
            # No siblings remain, point to parent
            path = path.parent()
        elif path.row() == sibling_count:
            # Has siblings but was last child, point to previous sibling
            path = path.previous_sibling()

        self._push_command(before, after, path, "Delete Requirement")

    def _on_shift_up_pressed(self) -> None:
        # Can't shift root
        if self._active_is_root():
            return

        active: Requirement = self._active_item_index.data(ROLE)
        path = self._model.path_from_index(self._active_item_index)

        before: Requirement = self._model.build_requirement()
        assert isinstance(before, RequirementArrayBase)
        after_remove: Requirement = self._remove_at_path(before, path)
        assert isinstance(after_remove, RequirementArrayBase)

        if path.row() > 0:
            path = path.previous_sibling()
            sibling: Requirement = self._model.index_from_path(path).data(ROLE)
            if isinstance(sibling, RequirementArrayBase):
                # Ascend into sibling
                path = path.extend_with(len(sibling.items))
        elif len(path) > 1:
            path = path.parent()
        else:
            return

        after: Requirement = self._insert_at_path(after_remove, path, active)

        self._push_command(before, after, path, "Move Up")

    def _on_shift_down_pressed(self) -> None:
        # Can't shift root
        if self._active_is_root():
            return

        active: Requirement = self._active_item_index.data(ROLE)
        path = self._model.path_from_index(self._active_item_index)
        sibling_count: int = self._model.sibling_count(path)

        before: Requirement = self._model.build_requirement()
        assert isinstance(before, RequirementArrayBase)
        after_remove: Requirement = self._remove_at_path(before, path)
        assert isinstance(after_remove, RequirementArrayBase)

        if path.row() < sibling_count:
            sibling_path = path.next_sibling()
            sibling: Requirement = self._model.index_from_path(sibling_path).data(ROLE)
            if isinstance(sibling, RequirementArrayBase):
                # Descend into sibling
                path = path.extend_with(0)
            else:
                path = sibling_path
        elif len(path) > 1:
            path = path.parent().next_sibling()
        else:
            return

        after: Requirement = self._insert_at_path(after_remove, path, active)

        self._push_command(before, after, path, "Move Down")

    def _on_type_combo_changed(self, idx: int = -1) -> None:
        before: Requirement = self._model.build_requirement()
        path = self._model.path_from_index(self._active_item_index)
        changed: Requirement = self._change_requirement_type(
            self._active_item_index.data(ROLE), self._combo_type.currentData(ROLE)
        )
        after = changed
        if isinstance(before, RequirementArrayBase):
            after = self._replace_at_path(before, path, changed)

        self._push_command(before, after, path, "Change Type")

    def _on_editor_field_changed(self, requirement: Requirement) -> None:
        if self._active_is_array() and isinstance(requirement, RequirementArrayBase):
            # Preserve array items
            requirement = type(requirement)(self._active_item_index.data(ROLE).items, requirement.comment)

        before: Requirement = self._model.build_requirement()
        path = self._model.path_from_index(self._active_item_index)
        after = requirement
        if isinstance(before, RequirementArrayBase):
            after = self._replace_at_path(before, path, requirement)

        self._push_command(before, after, path, "Edit Requirement")

    def deleteLater(self) -> None:
        self._stacked_widget.deleteLater()
        self._combo_type.deleteLater()
