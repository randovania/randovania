from functools import partial
from typing import Optional, Iterable, List

from PySide2.QtCore import Qt
from PySide2.QtGui import QIntValidator
from PySide2.QtWidgets import QPushButton, QWidget, QGroupBox, QVBoxLayout, QLabel, QGridLayout, QHBoxLayout, QComboBox, \
    QLineEdit

from randovania.game_description.requirements import RequirementSet, RequirementList, IndividualRequirement
from randovania.game_description.resource_type import ResourceType
from randovania.game_description.resources import ResourceDatabase, ResourceInfo


def _create_resource_name_combo(resource_database: ResourceDatabase,
                                resource_type: ResourceType,
                                current_resource: Optional[ResourceInfo],
                                parent: QWidget,
                                ) -> QComboBox:
    """

    :param resource_database:
    :param current_resource:
    :param parent:
    :return:
    """

    resource_name_combo = QComboBox(parent)

    for resource in sorted(resource_database.get_by_type(resource_type), key=lambda x: x.long_name):
        resource_name_combo.addItem(resource.long_name, resource)
        if resource is current_resource:
            resource_name_combo.setCurrentIndex(resource_name_combo.count() - 1)

    return resource_name_combo


def _create_resource_type_combo(current_resource_type: ResourceType, parent: QWidget) -> QComboBox:
    """

    :param current_resource_type:
    :param parent:
    :return:
    """
    resource_type_combo = QComboBox(parent)

    for resource_type in ResourceType:
        if resource_type == ResourceType.PICKUP_INDEX:
            continue

        resource_type_combo.addItem(resource_type.name, resource_type)
        if resource_type is current_resource_type:
            resource_type_combo.setCurrentIndex(resource_type_combo.count() - 1)

    return resource_type_combo


class ItemRow:
    def __init__(self,
                 parent: QWidget, parent_layout: QVBoxLayout,
                 resource_database: ResourceDatabase, item: IndividualRequirement,
                 rows: List["ItemRow"]
                 ):
        self.parent = parent
        self.resource_database = resource_database
        self._rows = rows
        rows.append(self)

        self.layout = QHBoxLayout(parent)
        parent_layout.addLayout(self.layout)

        self.resource_type_combo = _create_resource_type_combo(item.resource.resource_type, parent)
        self.resource_type_combo.setMinimumWidth(75)
        self.resource_type_combo.setMaximumWidth(75)

        self.resource_name_combo = _create_resource_name_combo(self.resource_database,
                                                               item.resource.resource_type,
                                                               item.resource,
                                                               self.parent)

        self.negate_combo = QComboBox(parent)
        self.negate_combo.addItem(">=", False)
        self.negate_combo.addItem("<", True)
        self.negate_combo.setCurrentIndex(int(item.negate))
        self.negate_combo.setMinimumWidth(40)
        self.negate_combo.setMaximumWidth(40)

        self.amount_edit = QLineEdit(parent)
        self.amount_edit.setValidator(QIntValidator(1, 10000))
        self.amount_edit.setText(str(item.amount))
        self.amount_edit.setMinimumWidth(45)
        self.amount_edit.setMaximumWidth(45)

        self.remove_button = QPushButton(parent)
        self.remove_button.setText("X")
        self.remove_button.setMaximumWidth(20)

        self.layout.addWidget(self.resource_type_combo)
        self.layout.addWidget(self.resource_name_combo)
        self.layout.addWidget(self.negate_combo)
        self.layout.addWidget(self.amount_edit)
        self.layout.addWidget(self.remove_button)

        self.resource_type_combo.currentIndexChanged.connect(self._update_type)
        self.remove_button.clicked.connect(self._delete_row)

    def _update_type(self):
        old_combo = self.resource_name_combo
        self.resource_name_combo = _create_resource_name_combo(self.resource_database,
                                                               self.resource_type_combo.currentData(),
                                                               None,
                                                               self.parent)

        self.layout.replaceWidget(old_combo, self.resource_name_combo)
        old_combo.deleteLater()

    def _delete_row(self):
        self.resource_type_combo.deleteLater()
        self.resource_name_combo.deleteLater()
        self.negate_combo.deleteLater()
        self.amount_edit.deleteLater()
        self.remove_button.deleteLater()
        self.layout.deleteLater()
        self._rows.remove(self)

    @property
    def current_individual(self) -> IndividualRequirement:
        return IndividualRequirement(
            self.resource_name_combo.currentData(),
            int(self.amount_edit.text()),
            self.negate_combo.currentData()
        )


class ConnectionsVisualizer:
    parent: QWidget
    resource_database: ResourceDatabase
    edit_mode: bool
    grid_layout: QGridLayout
    _elements: List[QWidget]
    num_columns_for_alternatives: int

    _current_last_index: int = 0

    def __init__(self,
                 parent: QWidget,
                 grid_layout: QGridLayout,
                 resource_database: ResourceDatabase,
                 requirement_set: Optional[RequirementSet],
                 edit_mode: bool,
                 num_columns_for_alternatives: int = 2
                 ):
        assert requirement_set != RequirementSet.impossible()

        self.parent = parent
        self.resource_database = resource_database
        self.edit_mode = edit_mode
        self.grid_layout = grid_layout
        self._elements = []
        self.num_columns_for_alternatives = num_columns_for_alternatives

        if requirement_set is not None:
            empty = True
            for alternative in requirement_set.alternatives:
                if alternative.items or self.edit_mode:
                    empty = False
                    self._add_box_with_requirements(alternative)

            if empty and not self.edit_mode:
                self._add_box_with_labels(["Trivial."])

        elif not self.edit_mode:
            self._add_box_with_labels(["Impossible to Reach."])

    def _add_element_to_grid(self, element: QWidget, index: int = None):
        if index is None:
            index = self._current_last_index
        self.grid_layout.addWidget(element,
                                   index // self.num_columns_for_alternatives,
                                   index % self.num_columns_for_alternatives)

    def _create_box_in_grid(self) -> QGroupBox:
        group_box = QGroupBox(self.parent)
        self._elements.append(group_box)
        self._add_element_to_grid(group_box)
        self._current_last_index += 1
        return group_box

    def _add_box_with_labels(self, labels: Iterable[str]) -> QGroupBox:
        group_box = self._create_box_in_grid()

        vertical_layout = QVBoxLayout(group_box)
        vertical_layout.setAlignment(Qt.AlignTop)
        vertical_layout.setContentsMargins(11, 11, 11, 11)
        vertical_layout.setSpacing(6)
        group_box.vertical_layout = vertical_layout

        for text in labels:
            label = QLabel(group_box)
            label.setText(text)
            vertical_layout.addWidget(label)

        return group_box

    def _add_box_with_requirements(self, alternative: RequirementList):
        group_box = self._create_box_in_grid()
        group_box.rows = []

        vertical_layout = QVBoxLayout(group_box)
        vertical_layout.setAlignment(Qt.AlignTop)

        for item in sorted(alternative.items):
            if self.edit_mode:
                ItemRow(group_box, vertical_layout, self.resource_database, item, group_box.rows)
            else:
                label = QLabel(group_box)
                label.setText(str(item))
                vertical_layout.addWidget(label)

        if self.edit_mode:
            tools_layout = QHBoxLayout(group_box)
            vertical_layout.addLayout(tools_layout)

            add_new_button = QPushButton(group_box)
            add_new_button.setText("New Requirement")
            tools_layout.addWidget(add_new_button)

            delete_button = QPushButton(group_box)
            delete_button.setText("Delete")
            delete_button.clicked.connect(partial(self._delete_alternative, group_box))
            tools_layout.addWidget(delete_button)

            def _new_row():
                empty_item = IndividualRequirement(
                    self.resource_database.get_by_type(ResourceType.ITEM)[0],
                    1, False
                )
                ItemRow(group_box, vertical_layout, self.resource_database, empty_item, group_box.rows)
                vertical_layout.removeItem(tools_layout)
                vertical_layout.addLayout(tools_layout)

            add_new_button.clicked.connect(_new_row)

        return group_box

    def new_alternative(self):
        self._add_box_with_requirements(RequirementList(0, []))

    def _delete_alternative(self, group: QGroupBox):
        index = self._elements.index(group)
        assert index is not None
        del self._elements[index]
        group.deleteLater()

    def deleteLater(self):
        for element in self._elements:
            element.deleteLater()

    def build_requirement_set(self) -> Optional[RequirementSet]:
        return RequirementSet(
            [
                RequirementList.without_misc_resources(
                    [
                        row.current_individual
                        for row in element.rows
                    ],
                    self.resource_database
                )
                for element in self._elements
            ]
        )
