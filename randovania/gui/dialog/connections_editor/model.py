from PySide6.QtCore import QModelIndex, QPersistentModelIndex, Qt, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel

from randovania.game_description.requirements.array_base import RequirementArrayBase
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.node_requirement import NodeRequirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_template import RequirementTemplate
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.resource_type import ResourceType
from randovania.layout.base.trick_level import LayoutTrickLevel

from .path import Path

ROLE = Qt.ItemDataRole.UserRole


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
        item.setData(requirement, ROLE)
        return item

    def path_from_index(self, index: QModelIndex) -> Path:
        """Builds a Path to the given index by walking up the tree, discarding the invisible root item"""
        path = Path()
        while index.isValid():
            path = path.extend_with(index.row())
            index = index.parent()
        # Current Path is in reverse order, parent() removes the last index (invisible root)
        return path.parent().reversed()

    def index_from_path(self, path: Path) -> QModelIndex:
        """Returns the model index at the given Path"""
        index = QModelIndex()
        for row in path.prefixed_with(0):  # Re-add index for invisible root
            next_index = self.index(row, 0, index)
            if not next_index.isValid():
                return index  # Fallback to deepest valid ancenstor
            index = next_index
        return index

    def sibling_count(self, path: Path) -> int:
        index = self.index_from_path(path)
        return self.itemFromIndex(index).parent().rowCount() - 1

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
            requirement: Requirement = item.data(ROLE)

            if isinstance(requirement, RequirementArrayBase):
                children = [walk(item.child(idx)) for idx in range(item.rowCount())]
                return type(requirement)(children, requirement.comment)

            return requirement

        return walk(self.invisibleRootItem().child(0))

    def flags(self, index: QModelIndex | QPersistentModelIndex) -> Qt.ItemFlag:
        """Overrides Qt's default item flags"""
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

        # if index.parent().isValid():
        #    flags |= Qt.ItemFlag.ItemIsDragEnabled

        # requirement = self.itemFromIndex(index).data(ROLE)
        # if isinstance(requirement, RequirementArrayBase):
        #    flags |= Qt.ItemFlag.ItemIsDropEnabled

        return flags
