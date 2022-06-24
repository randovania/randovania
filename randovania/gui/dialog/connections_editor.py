import typing

from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QDialog
from PySide6.QtWidgets import QPushButton, QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QComboBox, \
    QLineEdit

from randovania.game_description.requirements.array_base import RequirementArrayBase
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_or import RequirementOr
from randovania.game_description.requirements.requirement_template import RequirementTemplate
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceInfo
from randovania.game_description.resources.resource_type import ResourceType
from randovania.gui.generated.connections_editor_ui import Ui_ConnectionEditor
from randovania.gui.lib.common_qt_lib import set_default_window_icon
from randovania.gui.lib.scroll_protected import ScrollProtectedComboBox
from randovania.layout.base.trick_level import LayoutTrickLevel
from randovania.lib.enum_lib import iterate_enum


def _create_resource_name_combo(resource_database: ResourceDatabase,
                                resource_type: ResourceType,
                                current_resource: ResourceInfo | None,
                                parent: QWidget,
                                ) -> QComboBox:
    """

    :param resource_database:
    :param current_resource:
    :param parent:
    :return:
    """

    resource_name_combo = ScrollProtectedComboBox(parent)

    for resource in sorted(resource_database.get_by_type(resource_type), key=lambda x: x.long_name):
        resource_name_combo.addItem(resource.long_name, resource)
        if resource is current_resource:
            resource_name_combo.setCurrentIndex(resource_name_combo.count() - 1)

    return resource_name_combo


def _create_resource_type_combo(current_resource_type: ResourceType, parent: QWidget,
                                resource_database: ResourceDatabase) -> QComboBox:
    """

    :param current_resource_type:
    :param parent:
    :return:
    """
    resource_type_combo = ScrollProtectedComboBox(parent)

    for resource_type in iterate_enum(ResourceType):
        try:
            count_elements = len(resource_database.get_by_type(resource_type))
        except ValueError:
            count_elements = 0

        if count_elements == 0:
            continue

        resource_type_combo.addItem(resource_type.name, resource_type)
        if resource_type is current_resource_type:
            resource_type_combo.setCurrentIndex(resource_type_combo.count() - 1)

    return resource_type_combo


def _create_default_resource_requirement(resource_database: ResourceDatabase) -> ResourceRequirement:
    return ResourceRequirement.simple(
        resource_database.get_by_type(ResourceType.ITEM)[0],
    )


def _create_default_template_requirement(resource_database: ResourceDatabase) -> RequirementTemplate:
    template_name = None
    for template_name in resource_database.requirement_template.keys():
        break
    if template_name is None:
        raise RuntimeError("No templates?!")
    return RequirementTemplate(template_name)


class ResourceRequirementEditor:
    def __init__(self,
                 parent: QWidget, layout: QHBoxLayout,
                 resource_database: ResourceDatabase, item: ResourceRequirement,
                 ):
        self.parent = parent
        self.layout = layout
        self.resource_database = resource_database

        self.resource_type_combo = _create_resource_type_combo(item.resource.resource_type, parent, resource_database)
        self.resource_type_combo.setMinimumWidth(75)
        self.resource_type_combo.setMaximumWidth(75)

        self.resource_name_combo = _create_resource_name_combo(self.resource_database,
                                                               item.resource.resource_type,
                                                               item.resource,
                                                               self.parent)

        self.negate_combo = ScrollProtectedComboBox(parent)
        self.negate_combo.addItem("≥", False)
        self.negate_combo.addItem("<", True)
        self.negate_combo.setCurrentIndex(int(item.negate))
        self.negate_combo.setMinimumWidth(40)
        self.negate_combo.setMaximumWidth(40)

        self.negate_check = QtWidgets.QCheckBox(parent)
        self.negate_check.setChecked(item.negate)

        self.amount_edit = QLineEdit(parent)
        self.amount_edit.setValidator(QIntValidator(1, 10000))
        self.amount_edit.setText(str(item.amount))
        self.amount_edit.setMinimumWidth(45)
        self.amount_edit.setMaximumWidth(45)

        self.amount_combo = ScrollProtectedComboBox(parent)
        for trick_level in iterate_enum(LayoutTrickLevel):
            self.amount_combo.addItem(trick_level.long_name, userData=trick_level.as_number)
        self.amount_combo.setCurrentIndex(self.amount_combo.findData(item.amount))

        for widget in self._all_widgets:
            self.layout.addWidget(widget)

        self.resource_type_combo.currentIndexChanged.connect(self._update_type)
        self._update_visible_elements_by_type()

    @property
    def resource_type(self) -> ResourceType:
        return self.resource_type_combo.currentData()

    def _update_visible_elements_by_type(self):
        resource_type = self.resource_type

        if resource_type == ResourceType.DAMAGE:
            self.negate_combo.setCurrentIndex(0)

        self.negate_check.setText("Before" if resource_type == ResourceType.EVENT else "Not")
        self.negate_check.setVisible(resource_type in {ResourceType.EVENT, ResourceType.VERSION, ResourceType.MISC})
        self.negate_combo.setVisible(resource_type in {ResourceType.ITEM, ResourceType.DAMAGE})
        self.negate_combo.setEnabled(resource_type == ResourceType.ITEM)
        self.amount_edit.setVisible(resource_type in {ResourceType.ITEM, ResourceType.DAMAGE})
        self.amount_combo.setVisible(resource_type == ResourceType.TRICK)

    def _update_type(self):
        old_combo = self.resource_name_combo

        self.resource_name_combo = _create_resource_name_combo(self.resource_database,
                                                               self.resource_type_combo.currentData(),
                                                               None,
                                                               self.parent)

        self.layout.replaceWidget(old_combo, self.resource_name_combo)
        old_combo.deleteLater()
        self._update_visible_elements_by_type()

    def deleteLater(self):
        for widget in self._all_widgets:
            widget.deleteLater()

    @property
    def _all_widgets(self) -> typing.Iterable[QWidget]:
        yield self.resource_type_combo
        yield self.negate_check
        yield self.resource_name_combo
        yield self.negate_combo
        yield self.amount_edit
        yield self.amount_combo

    @property
    def current_requirement(self) -> ResourceRequirement:
        resource_type = self.resource_type

        # Quantity
        if resource_type == ResourceType.TRICK:
            quantity: int = self.amount_combo.currentData()
        elif resource_type == ResourceType.EVENT:
            quantity = 1
        else:
            quantity = int(self.amount_edit.text())

        # Negate flag
        if resource_type == ResourceType.ITEM:
            negate: bool = self.negate_combo.currentData()
        elif resource_type == ResourceType.EVENT:
            negate = self.negate_check.isChecked()
        else:
            negate = False

        return ResourceRequirement.create(self.resource_name_combo.currentData(), quantity, negate)


class ArrayRequirementEditor:
    def __init__(self, parent: QWidget, parent_layout: QVBoxLayout, line_layout: QHBoxLayout,
                 resource_database: ResourceDatabase, requirement: RequirementArrayBase):
        self._editors = []
        self.resource_database = resource_database
        self._array_type = type(requirement)

        # the parent is added to a layout which is added to parent_layout, so we
        index = parent_layout.indexOf(line_layout) + 1

        self.group_box = QGroupBox(parent)
        self.group_box.setStyleSheet("QGroupBox { margin-top: 2px; }")
        parent_layout.insertWidget(index, self.group_box)
        self.item_layout = QVBoxLayout(self.group_box)
        self.item_layout.setContentsMargins(8, 2, 2, 6)
        self.item_layout.setAlignment(Qt.AlignTop)

        self.new_item_button = QPushButton(self.group_box)
        self.new_item_button.setMaximumWidth(75)
        self.new_item_button.setText("New Row")
        self.new_item_button.clicked.connect(self.new_item)

        self.comment_text_box = QLineEdit(parent)
        self.comment_text_box.setText(requirement.comment or "")
        self.comment_text_box.setPlaceholderText("Comment")
        line_layout.addWidget(self.comment_text_box)

        for item in requirement.items:
            self._create_item(item)

        self.item_layout.addWidget(self.new_item_button)

    def _create_item(self, item: Requirement):
        def on_remove():
            self._editors.remove(nested_editor)
            nested_editor.deleteLater()

        nested_editor = RequirementEditor(self.group_box, self.item_layout, self.resource_database, on_remove=on_remove)
        nested_editor.create_specialized_editor(item)
        self._editors.append(nested_editor)

    def new_item(self):
        self._create_item(_create_default_resource_requirement(self.resource_database))

        self.item_layout.removeWidget(self.new_item_button)
        self.item_layout.addWidget(self.new_item_button)

    def deleteLater(self):
        self.group_box.deleteLater()
        self.comment_text_box.deleteLater()
        for editor in self._editors:
            editor.deleteLater()
        self.new_item_button.deleteLater()

    @property
    def current_requirement(self) -> RequirementArrayBase:
        comment = self.comment_text_box.text().strip()
        if comment == "":
            comment = None

        return self._array_type(
            [
                editor.current_requirement
                for editor in self._editors
            ],
            comment=comment,
        )


class TemplateRequirementEditor:
    def __init__(self,
                 parent: QWidget, layout: QHBoxLayout,
                 resource_database: ResourceDatabase, item: RequirementTemplate,
                 ):
        self.parent = parent
        self.layout = layout
        self.resource_database = resource_database

        template_name_combo = QComboBox(parent)

        for template_name in sorted(resource_database.requirement_template.keys()):
            template_name_combo.addItem(template_name)
            if template_name == item.template_name:
                template_name_combo.setCurrentIndex(template_name_combo.count() - 1)

        self.template_name_combo = template_name_combo
        self.layout.addWidget(self.template_name_combo)

    def deleteLater(self):
        self.template_name_combo.deleteLater()

    @property
    def current_requirement(self) -> RequirementTemplate:
        return RequirementTemplate(self.template_name_combo.currentText())


class RequirementEditor:
    _editor: None | ResourceRequirementEditor | ArrayRequirementEditor | TemplateRequirementEditor

    def __init__(self,
                 parent: QWidget,
                 parent_layout: QVBoxLayout,
                 resource_database: ResourceDatabase,
                 *, on_remove=None):

        self.parent = parent
        self.parent_layout = parent_layout
        self.resource_database = resource_database
        self._editor = None
        self._last_resource = None
        self._last_items = ()
        self._last_comment = None

        self.line_layout = QHBoxLayout()
        self.line_layout.setAlignment(Qt.AlignLeft)
        self.parent_layout.addLayout(self.line_layout)

        if on_remove is not None:
            self.remove_button = QtWidgets.QToolButton(parent)
            self.remove_button.setText("X")
            self.remove_button.setMaximumWidth(20)
            self.remove_button.clicked.connect(on_remove)
            self.line_layout.addWidget(self.remove_button)
        else:
            self.remove_button = None

        self.requirement_type_combo = QComboBox(parent)
        self.requirement_type_combo.addItem("Resource", ResourceRequirement)
        self.requirement_type_combo.addItem("Or", RequirementOr)
        self.requirement_type_combo.addItem("And", RequirementAnd)
        if resource_database.requirement_template:
            self.requirement_type_combo.addItem("Template", RequirementTemplate)
        self.requirement_type_combo.setMaximumWidth(75)
        self.requirement_type_combo.activated.connect(self._on_change_requirement_type)
        self.line_layout.addWidget(self.requirement_type_combo)

    def create_specialized_editor(self, requirement: Requirement):
        if isinstance(requirement, ResourceRequirement):
            requirement_type = ResourceRequirement
        else:
            requirement_type = type(requirement)
        self.requirement_type_combo.setCurrentIndex(self.requirement_type_combo.findData(requirement_type))

        if isinstance(requirement, ResourceRequirement):
            self._editor = ResourceRequirementEditor(self.parent, self.line_layout, self.resource_database, requirement)

        elif isinstance(requirement, RequirementArrayBase):
            self._editor = ArrayRequirementEditor(self.parent, self.parent_layout, self.line_layout,
                                                  self.resource_database, requirement)

        elif isinstance(requirement, RequirementTemplate):
            self._editor = TemplateRequirementEditor(self.parent, self.line_layout, self.resource_database, requirement)

        else:
            raise RuntimeError(f"Unknown requirement type: {type(requirement)} - {requirement}")

    def _on_change_requirement_type(self):
        current_requirement = self.current_requirement
        self._editor.deleteLater()

        if isinstance(current_requirement, ResourceRequirement):
            self._last_resource = current_requirement

        elif isinstance(current_requirement, RequirementArrayBase):
            self._last_items = current_requirement.items
            self._last_comment = current_requirement.comment

        elif isinstance(current_requirement, RequirementTemplate):
            pass

        else:
            raise RuntimeError(f"Unknown requirement type: {type(current_requirement)} - {current_requirement}")

        new_class = self.requirement_type_combo.currentData()
        if new_class == ResourceRequirement:
            if self._last_resource is None:
                new_requirement = _create_default_resource_requirement(self.resource_database)
            else:
                new_requirement = self._last_resource
        elif new_class == RequirementTemplate:
            new_requirement = _create_default_template_requirement(self.resource_database)
        else:
            new_requirement = new_class(self._last_items, self._last_comment)

        self.create_specialized_editor(new_requirement)

    def deleteLater(self):
        if self.remove_button is not None:
            self.remove_button.deleteLater()

        self.requirement_type_combo.deleteLater()

        if self._editor is not None:
            self._editor.deleteLater()

    @property
    def current_requirement(self) -> Requirement:
        return self._editor.current_requirement


class ConnectionsEditor(QDialog, Ui_ConnectionEditor):
    parent: QWidget
    resource_database: ResourceDatabase
    _elements: list[QWidget]

    def __init__(self, parent: QWidget, resource_database: ResourceDatabase, requirement: Requirement):
        super().__init__(parent)
        self.setupUi(self)
        set_default_window_icon(self)

        self.parent = parent
        self.resource_database = resource_database

        self.contents_layout.setAlignment(Qt.AlignTop)

        self._root_editor = RequirementEditor(self, self.contents_layout, resource_database)
        self._root_editor.create_specialized_editor(requirement)

    def deleteLater(self):
        self._root_editor.deleteLater()

    def build_requirement(self) -> Requirement:
        return self._root_editor.current_requirement

    @property
    def final_requirement(self) -> Requirement | None:
        result = self.build_requirement()
        if result == Requirement.impossible():
            return None
        return result
