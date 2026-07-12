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

    def _push_command(
        self, before: Requirement, after: Requirement, selection_path: list[int], description: str
    ) -> None:
        self._undo_stack.push(Command(self._model, self._view, before, after, selection_path, description))

    def _on_add_requirement_pressed(self) -> None:
        if self._active_item_index is None:
            return

        before: Requirement = self._model.build_requirement()

        # Root is not array type, can't add requirement
        if not self._active_item_index.parent().isValid() and not isinstance(before, RequirementArrayBase):
            return

        assert isinstance(before, RequirementArrayBase)
        path: list[int] = self._model.path_from_index(self._active_item_index)
        requirement_path = path[1:]
        row: int = path[-1]
        selected = self._active_item_index.data(ROLE)

        new_type = self._combo_type.currentData(ROLE)
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

        self._push_command(before, after, selection_path, "Add Requirement")

    def _on_delete_requirement_pressed(self) -> None:
        if self._active_item_index is None:
            return

        # Can't delete root
        if not self._active_item_index.parent().isValid():
            return

        before: Requirement = self._model.build_requirement()
        assert isinstance(before, RequirementArrayBase)
        path: list[int] = self._model.path_from_index(self._active_item_index)
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

        self._push_command(before, after, selection_path, "Delete Requirement")

    def _on_shift_up_pressed(self) -> None:
        if self._active_item_index is None:
            return

        # Can't shift root
        if not self._active_item_index.parent().isValid():
            return

        path: list[int] = self._model.path_from_index(self._active_item_index)
        requirement_path = path[1:]
        row: int = path[-1]

        selected: Requirement = self._active_item_index.data(ROLE)
        before: Requirement = self._model.build_requirement()
        assert isinstance(before, RequirementArrayBase)
        after_remove: Requirement = self._remove_at_path(before, requirement_path)
        assert isinstance(after_remove, RequirementArrayBase)

        if row > 0:
            # Next sibling exists
            row -= 1
            sibling_path: list[int] = [*path[:-1], row]
            sibling_requirement = self._model.index_from_path(sibling_path).data(ROLE)
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

        self._push_command(before, after, selection_path, "Move Up")

    def _on_shift_down_pressed(self) -> None:
        if self._active_item_index is None:
            return

        # Can't shift root
        if not self._active_item_index.parent().isValid():
            return

        path: list[int] = self._model.path_from_index(self._active_item_index)
        requirement_path = path[1:]
        row: int = path[-1]
        rows: int = self._model.itemFromIndex(self._active_item_index).parent().rowCount()

        selected: Requirement = self._active_item_index.data(ROLE)
        before: Requirement = self._model.build_requirement()
        assert isinstance(before, RequirementArrayBase)
        after_remove: Requirement = self._remove_at_path(before, requirement_path)
        assert isinstance(after_remove, RequirementArrayBase)

        if row < rows - 1:
            # Next sibling exists
            row += 1
            sibling_path: list[int] = [*path[:-1], row]
            if isinstance(self._model.index_from_path(sibling_path).data(ROLE), RequirementArrayBase):
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

        self._push_command(before, after, selection_path, "Move Down")

    def _on_type_combo_changed(self, idx: int = -1) -> None:
        if self._active_item_index is None:
            return

        before: Requirement = self._model.build_requirement()

        current: Requirement = self._active_item_index.data(ROLE)
        new_type: type = self._combo_type.currentData(ROLE)
        changed: Requirement = self._change_requirement_type(current, new_type)

        path: list[int] = self._model.path_from_index(self._active_item_index)
        after: Requirement = (
            self._replace_at_path(before, path[1:], changed) if isinstance(before, RequirementArrayBase) else changed
        )

        self._push_command(before, after, path, "Change Type")

    def _on_editor_field_changed(self, requirement: Requirement) -> None:
        if self._active_item_index is None:
            return

        current: Requirement = self._active_item_index.data(ROLE)
        if isinstance(requirement, RequirementArrayBase) and isinstance(current, RequirementArrayBase):
            requirement.items = current.items

        before: Requirement = self._model.build_requirement()
        path: list[int] = self._model.path_from_index(self._active_item_index)
        after: Requirement = (
            self._replace_at_path(before, path[1:], requirement)
            if isinstance(before, RequirementArrayBase)
            else requirement
        )

        self._push_command(before, after, path, "Edit Requirement")

    def deleteLater(self) -> None:
        self._stacked_widget.deleteLater()
        self._combo_type.deleteLater()
