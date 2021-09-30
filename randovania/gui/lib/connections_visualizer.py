import re
from typing import Optional, List, Tuple

from PySide2.QtCore import Qt
from PySide2.QtGui import QIntValidator
from PySide2.QtWidgets import QPushButton, QWidget, QGroupBox, QVBoxLayout, QLabel, QGridLayout, QHBoxLayout, QComboBox, \
    QLineEdit

import randovania.game_description.pretty_print
from randovania.game_description.requirements import ResourceRequirement, Requirement
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceInfo
from randovania.game_description.resources.resource_type import ResourceType


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
        if not resource_type.is_usable_for_requirement:
            continue

        resource_type_combo.addItem(resource_type.name, resource_type)
        if resource_type is current_resource_type:
            resource_type_combo.setCurrentIndex(resource_type_combo.count() - 1)

    return resource_type_combo


class ItemRow:
    def __init__(self,
                 parent: QWidget, parent_layout: QVBoxLayout,
                 resource_database: ResourceDatabase, item: ResourceRequirement,
                 rows: List["ItemRow"]
                 ):
        self.parent = parent
        self.resource_database = resource_database
        self._rows = rows
        rows.append(self)

        self.layout = QHBoxLayout()
        self.layout.setObjectName(f"Box layout for {item.resource.long_name}")
        parent_layout.addLayout(self.layout)

        self.resource_type_combo = _create_resource_type_combo(item.resource.resource_type, parent)
        self.resource_type_combo.setMinimumWidth(75)
        self.resource_type_combo.setMaximumWidth(75)

        self.resource_name_combo = _create_resource_name_combo(self.resource_database,
                                                               item.resource.resource_type,
                                                               item.resource,
                                                               self.parent)

        self.negate_combo = QComboBox(parent)
        self.negate_combo.addItem("≥", False)
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
    def current_individual(self) -> ResourceRequirement:
        return ResourceRequirement(
            self.resource_name_combo.currentData(),
            int(self.amount_edit.text()),
            self.negate_combo.currentData()
        )


class ConnectionsVisualizer:
    parent: QWidget
    resource_database: ResourceDatabase
    grid_layout: QGridLayout
    _elements: List[QWidget]

    def __init__(self,
                 parent: QWidget,
                 grid_layout: QGridLayout,
                 resource_database: ResourceDatabase,
                 requirement: Requirement,
                 edit_mode: bool
                 ):
        self.parent = parent
        self.resource_database = resource_database
        self.edit_mode = edit_mode
        self.grid_layout = grid_layout
        self._elements = []

        self._add_widget_for_requirement_array(requirement)

    def _add_widget_for_requirement_array(self, requirement: Requirement):
        self.grid_layout.setAlignment(Qt.AlignTop)

        parents: List[Tuple[QGroupBox, QVBoxLayout]] = [(self.parent, self.grid_layout)]

        for depth, text in randovania.game_description.pretty_print.pretty_print_requirement(requirement):
            if "of the following" in text:
                parent = parents[depth]
                group_box = QGroupBox(parent[0])
                group_box.setContentsMargins(8, 0, 2, 6)
                group_box.setTitle(text)
                self._elements.append(group_box)
                vertical_layout = QVBoxLayout(group_box)
                vertical_layout.setAlignment(Qt.AlignTop)
                parent[1].addWidget(group_box)
                if len(parents) <= depth + 1:
                    parents.append(None)
                parents[depth + 1] = (group_box, vertical_layout)
            else:
                label = QLabel(parents[depth][0])

                # This is a comment!
                if text.startswith("# "):
                    text = re.sub(r"(https?://[^\s]+)", r'<a href="\1">\1</a>', text[2:])
                    label.setStyleSheet("font-weight: bold; color: green")
                    label.setOpenExternalLinks(True)

                label.setText(text)
                label.setWordWrap(True)
                self._elements.append(label)
                parents[depth][1].addWidget(label)

    def deleteLater(self):
        for element in self._elements:
            element.deleteLater()
