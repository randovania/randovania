from __future__ import annotations

import typing

from PySide6 import QtGui, QtWidgets
from PySide6.QtCore import Qt

from randovania.game_description.db.resource_node import ResourceNode
from randovania.game_description.requirements.array_base import RequirementArrayBase
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.node_requirement import NodeRequirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_or import RequirementOr
from randovania.game_description.requirements.requirement_template import RequirementTemplate
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.resource_type import ResourceType
from randovania.gui.generated.connections_editor_ui import Ui_ConnectionEditor
from randovania.gui.lib import signal_handling
from randovania.gui.lib.common_qt_lib import set_default_window_icon
from randovania.gui.lib.scroll_protected import ScrollProtectedComboBox
from randovania.gui.widgets.node_selector_widget import NodeSelectorWidget
from randovania.layout.base.trick_level import LayoutTrickLevel
from randovania.lib.enum_lib import iterate_enum

if typing.TYPE_CHECKING:
    from randovania.game_description.db.region_list import RegionList
    from randovania.game_description.resources.resource_database import NamedRequirementTemplate, ResourceDatabase
    from randovania.game_description.resources.resource_info import ResourceInfo


def _create_resource_name_combo(
    resource_database: ResourceDatabase,
    resource_type: ResourceType,
    current_resource: ResourceInfo | None,
    parent: QtWidgets.QWidget,
) -> QtWidgets.QComboBox:
    """

    :param resource_database:
    :param current_resource:
    :param parent:
    :return:
    """

    resource_name_combo = ScrollProtectedComboBox(parent)

    sorted_resources: list[ResourceInfo] = sorted(
        resource_database.get_by_type(resource_type), key=lambda x: x.long_name
    )
    for resource in sorted_resources:
        resource_name_combo.addItem(resource.long_name, resource)
        if resource is current_resource:
            resource_name_combo.setCurrentIndex(resource_name_combo.count() - 1)

    return resource_name_combo


def _create_resource_type_combo(
    current_resource_type: ResourceType, parent: QtWidgets.QWidget, resource_database: ResourceDatabase
) -> QtWidgets.QComboBox:
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


def _create_default_node_requirement(region_list: RegionList) -> NodeRequirement:
    for node in region_list.all_nodes:
        if isinstance(node, ResourceNode):
            return NodeRequirement(node.identifier)
    raise RuntimeError("No nodes?!")


class BaseEditor:
    def delete_later(self) -> None:
        raise NotImplementedError

    @property
    def current_requirement(self) -> Requirement | None:
        raise NotImplementedError

    def requirement_type(self) -> type[Requirement]:
        raise NotImplementedError


class ResourceRequirementEditor(BaseEditor):
    def __init__(
        self,
        parent: QtWidgets.QWidget,
        layout: QtWidgets.QHBoxLayout,
        resource_database: ResourceDatabase,
        item: ResourceRequirement,
    ):
        self.parent_widget = parent
        self.layout = layout
        self.resource_database = resource_database

        self.resource_type_combo = _create_resource_type_combo(item.resource.resource_type, parent, resource_database)
        self.resource_type_combo.setMinimumWidth(75)
        self.resource_type_combo.setMaximumWidth(75)

        self.resource_name_combo = _create_resource_name_combo(
            self.resource_database, item.resource.resource_type, item.resource, self.parent_widget
        )

        self.negate_combo = ScrollProtectedComboBox(parent)
        self.negate_combo.addItem("≥", False)
        self.negate_combo.addItem("<", True)
        self.negate_combo.setCurrentIndex(int(item.negate))
        self.negate_combo.setMinimumWidth(40)
        self.negate_combo.setMaximumWidth(40)

        self.negate_check = QtWidgets.QCheckBox(parent)
        self.negate_check.setChecked(item.negate)

        self.amount_edit = QtWidgets.QLineEdit(parent)
        self.amount_edit.setValidator(QtGui.QIntValidator(1, 10000))
        self.amount_edit.setText(str(item.amount))
        self.amount_edit.setMinimumWidth(45)
        self.amount_edit.setMaximumWidth(45)

        self.amount_combo = ScrollProtectedComboBox(parent)
        for trick_level in iterate_enum(LayoutTrickLevel):
            self.amount_combo.addItem(trick_level.long_name, userData=trick_level.as_number)
        signal_handling.set_combo_with_value(self.amount_combo, item.amount)

        for widget in self._all_widgets:
            self.layout.addWidget(widget)

        self.resource_type_combo.currentIndexChanged.connect(self._update_type)
        self._update_visible_elements_by_type()

    @property
    def resource_type(self) -> ResourceType:
        return self.resource_type_combo.currentData()

    def _update_visible_elements_by_type(self) -> None:
        resource_type = self.resource_type

        if resource_type == ResourceType.DAMAGE:
            self.negate_combo.setCurrentIndex(0)

        self.negate_check.setText("Before" if resource_type == ResourceType.EVENT else "Not")
        self.negate_check.setVisible(resource_type in {ResourceType.EVENT, ResourceType.VERSION, ResourceType.MISC})
        self.negate_combo.setVisible(resource_type in {ResourceType.ITEM, ResourceType.DAMAGE})
        self.negate_combo.setEnabled(resource_type == ResourceType.ITEM)
        self.amount_edit.setVisible(resource_type in {ResourceType.ITEM, ResourceType.DAMAGE})
        self.amount_combo.setVisible(resource_type == ResourceType.TRICK)

    def _update_type(self) -> None:
        old_combo = self.resource_name_combo

        self.resource_name_combo = _create_resource_name_combo(
            self.resource_database, self.resource_type_combo.currentData(), None, self.parent_widget
        )

        self.layout.replaceWidget(old_combo, self.resource_name_combo)
        old_combo.deleteLater()
        self._update_visible_elements_by_type()

    def delete_later(self) -> None:
        for widget in self._all_widgets:
            widget.deleteLater()

    @property
    def _all_widgets(self) -> typing.Iterable[QtWidgets.QWidget]:
        yield self.resource_type_combo
        yield self.negate_check
        yield self.resource_name_combo
        yield self.negate_combo
        yield self.amount_edit
        yield self.amount_combo

    @property
    def current_requirement(self) -> Requirement:
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
        elif resource_type in {ResourceType.EVENT, ResourceType.MISC}:
            negate = self.negate_check.isChecked()
        else:
            negate = False

        return ResourceRequirement.create(self.resource_name_combo.currentData(), quantity, negate)

    def requirement_type(self) -> type[Requirement]:
        return ResourceRequirement


class ArrayRequirementEditor(BaseEditor):
    _editors: list[RequirementEditor]

    def __init__(
        self,
        parent: QtWidgets.QWidget,
        parent_layout: QtWidgets.QVBoxLayout,
        line_layout: QtWidgets.QHBoxLayout,
        resource_database: ResourceDatabase,
        region_list: RegionList,
        requirement: RequirementArrayBase,
    ):
        self._editors = []
        self.resource_database = resource_database
        self.region_list = region_list
        self._array_type = type(requirement)

        # the parent is added to a layout which is added to parent_layout, so we
        index = parent_layout.indexOf(line_layout) + 1

        self.group_box = QtWidgets.QGroupBox(parent)
        self.group_box.setStyleSheet("QGroupBox { margin-top: 2px; }")
        parent_layout.insertWidget(index, self.group_box)
        self.item_layout = QtWidgets.QVBoxLayout(self.group_box)
        self.item_layout.setContentsMargins(8, 2, 2, 6)
        self.item_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.new_item_button = QtWidgets.QPushButton(self.group_box)
        self.new_item_button.setMaximumWidth(75)
        self.new_item_button.setText("New Row")
        self.new_item_button.clicked.connect(self.new_item)

        self.comment_text_box = QtWidgets.QLineEdit(parent)
        self.comment_text_box.setText(requirement.comment or "")
        self.comment_text_box.setPlaceholderText("Comment")
        line_layout.addWidget(self.comment_text_box)

        for item in requirement.items:
            self._create_item(item)

        self.item_layout.addWidget(self.new_item_button)

    def _create_item(self, item: Requirement) -> None:
        def on_remove() -> None:
            self._editors.remove(nested_editor)
            nested_editor.delete_later()

        nested_editor = RequirementEditor(
            self.group_box, self.item_layout, self.resource_database, self.region_list, on_remove=on_remove
        )
        nested_editor.create_specialized_editor(item)
        self._editors.append(nested_editor)

    def new_item(self) -> None:
        self._create_item(_create_default_resource_requirement(self.resource_database))

        self.item_layout.removeWidget(self.new_item_button)
        self.item_layout.addWidget(self.new_item_button)

    def delete_later(self) -> None:
        self.group_box.deleteLater()
        self.comment_text_box.deleteLater()
        for editor in self._editors:
            editor.delete_later()
        self.new_item_button.deleteLater()

    @property
    def current_requirement(self) -> RequirementArrayBase | None:
        comment: str | None = self.comment_text_box.text().strip()
        if comment == "":
            comment = None

        nested: list[Requirement] = []
        for editor in self._editors:
            req = editor.current_requirement
            if req is None:
                return None
            nested.append(req)

        return self._array_type(nested, comment=comment)

    def requirement_type(self) -> type[Requirement]:
        return self._array_type


class TemplateRequirementEditor(BaseEditor):
    def __init__(
        self,
        parent: QtWidgets.QWidget,
        layout: QtWidgets.QHBoxLayout,
        resource_database: ResourceDatabase,
        item: RequirementTemplate,
    ):
        self.parent = parent
        self.layout = layout
        self.resource_database = resource_database

        template_name_combo = QtWidgets.QComboBox(parent)

        def key_get(it: tuple[str, NamedRequirementTemplate]) -> str:
            return it[1].display_name

        for template_name, template in sorted(resource_database.requirement_template.items(), key=key_get):
            template_name_combo.addItem(template.display_name, template_name)
            if template_name == item.template_name:
                template_name_combo.setCurrentIndex(template_name_combo.count() - 1)

        self.template_name_combo = template_name_combo
        self.layout.addWidget(self.template_name_combo)

    def delete_later(self) -> None:
        self.template_name_combo.deleteLater()

    @property
    def current_requirement(self) -> RequirementTemplate:
        return RequirementTemplate(self.template_name_combo.currentData())

    def requirement_type(self) -> type[Requirement]:
        return RequirementTemplate


class NodeRequirementEditor(BaseEditor):
    def __init__(
        self,
        parent: QtWidgets.QWidget,
        layout: QtWidgets.QHBoxLayout,
        region_list: RegionList,
        item: NodeRequirement,
    ):
        self.parent = parent
        self.layout = layout
        self.selector = NodeSelectorWidget(
            region_list, lambda node: isinstance(node, ResourceNode) and not node.is_derived_node
        )
        self.selector.select_by_identifier(item.node_identifier)

        self.layout.addWidget(self.selector)

    def delete_later(self) -> None:
        self.selector.deleteLater()

    @property
    def current_requirement(self) -> NodeRequirement | None:
        selected_node = self.selector.selected_node()
        if selected_node is not None:
            return NodeRequirement(selected_node.identifier)
        return None

    def requirement_type(self) -> type[Requirement]:
        return NodeRequirement


class RequirementEditor:
    remove_button: QtWidgets.QToolButton | None
    _editor: BaseEditor | None
    # for ResourceRequirement
    _last_resource: Requirement | None
    # for RequirementArrayBase
    _last_items: tuple[Requirement, ...] = ()
    _last_comment: str | None

    def __init__(
        self,
        parent: QtWidgets.QWidget,
        parent_layout: QtWidgets.QVBoxLayout,
        resource_database: ResourceDatabase,
        region_list: RegionList,
        *,
        on_remove: typing.Callable[[], None] | None = None,
    ):
        self.parent = parent
        self.parent_layout = parent_layout
        self.resource_database = resource_database
        self.region_list = region_list
        self._editor = None
        self._last_resource = None
        self._last_items = ()
        self._last_comment = None

        self.line_layout = QtWidgets.QHBoxLayout()
        self.line_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.parent_layout.addLayout(self.line_layout)

        if on_remove is not None:
            self.remove_button = QtWidgets.QToolButton(parent)
            self.remove_button.setText("X")
            self.remove_button.setMaximumWidth(20)
            self.remove_button.clicked.connect(on_remove)
            self.line_layout.addWidget(self.remove_button)
        else:
            self.remove_button = None

        self.requirement_type_combo = QtWidgets.QComboBox(parent)
        self.requirement_type_combo.addItem("Resource", ResourceRequirement)
        self.requirement_type_combo.addItem("Or", RequirementOr)
        self.requirement_type_combo.addItem("And", RequirementAnd)
        self.requirement_type_combo.addItem("Node", NodeRequirement)
        if resource_database.requirement_template:
            self.requirement_type_combo.addItem("Template", RequirementTemplate)
        self.requirement_type_combo.setMaximumWidth(75)
        self.requirement_type_combo.activated.connect(self._on_change_requirement_type)
        self.line_layout.addWidget(self.requirement_type_combo)

    def create_specialized_editor(self, requirement: Requirement) -> None:
        requirement_type: type[Requirement]
        if isinstance(requirement, ResourceRequirement):
            requirement_type = ResourceRequirement
        else:
            requirement_type = type(requirement)
        signal_handling.set_combo_with_value(self.requirement_type_combo, requirement_type)

        if isinstance(requirement, ResourceRequirement):
            self._editor = ResourceRequirementEditor(self.parent, self.line_layout, self.resource_database, requirement)

        elif isinstance(requirement, RequirementArrayBase):
            self._editor = ArrayRequirementEditor(
                self.parent, self.parent_layout, self.line_layout, self.resource_database, self.region_list, requirement
            )

        elif isinstance(requirement, RequirementTemplate):
            self._editor = TemplateRequirementEditor(self.parent, self.line_layout, self.resource_database, requirement)

        elif isinstance(requirement, NodeRequirement):
            self._editor = NodeRequirementEditor(self.parent, self.line_layout, self.region_list, requirement)

        else:
            raise RuntimeError(f"Unknown requirement type: {type(requirement)} - {requirement}")

    def _on_change_requirement_type(self) -> None:
        assert self._editor is not None
        current_requirement = self.current_requirement
        self._editor.delete_later()

        if isinstance(current_requirement, ResourceRequirement):
            self._last_resource = current_requirement

        elif isinstance(current_requirement, RequirementArrayBase):
            self._last_items = current_requirement.items
            self._last_comment = current_requirement.comment

        elif isinstance(current_requirement, RequirementTemplate):
            pass

        elif isinstance(current_requirement, NodeRequirement):
            pass

        elif current_requirement is not None:
            raise RuntimeError(f"Unknown requirement type: {type(current_requirement)} - {current_requirement}")

        new_requirement: Requirement
        new_class = self.requirement_type_combo.currentData()

        if new_class == ResourceRequirement:
            if self._last_resource is None:
                new_requirement = _create_default_resource_requirement(self.resource_database)
            else:
                new_requirement = self._last_resource

        elif new_class == RequirementTemplate:
            new_requirement = _create_default_template_requirement(self.resource_database)

        elif new_class == NodeRequirement:
            new_requirement = _create_default_node_requirement(self.region_list)
        else:
            new_requirement = new_class(self._last_items, self._last_comment)

        self.create_specialized_editor(new_requirement)

    def delete_later(self) -> None:
        if self.remove_button is not None:
            self.remove_button.deleteLater()

        self.requirement_type_combo.deleteLater()

        if self._editor is not None:
            self._editor.delete_later()

    @property
    def current_requirement(self) -> Requirement | None:
        assert self._editor is not None
        return self._editor.current_requirement


class ConnectionsEditor(QtWidgets.QDialog, Ui_ConnectionEditor):
    parent_widget: QtWidgets.QWidget
    resource_database: ResourceDatabase
    _elements: list[QtWidgets.QWidget]

    def __init__(
        self,
        parent: QtWidgets.QWidget,
        resource_database: ResourceDatabase,
        region_list: RegionList,
        requirement: Requirement,
    ):
        super().__init__(parent)
        self.setupUi(self)
        set_default_window_icon(self)

        self.parent_widget = parent
        self.resource_database = resource_database
        self.region_list = region_list

        self.contents_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._root_editor = RequirementEditor(self, self.contents_layout, resource_database, region_list)
        self._root_editor.create_specialized_editor(requirement)

    def deleteLater(self) -> None:
        self._root_editor.delete_later()

    def build_requirement(self) -> Requirement | None:
        return self._root_editor.current_requirement

    @property
    def final_requirement(self) -> Requirement | None:
        result = self.build_requirement()
        assert result is not None
        if result == Requirement.impossible():
            return None
        return result

    def accept(self) -> None:
        result = self.build_requirement()
        if result is None:
            QtWidgets.QMessageBox.critical(
                self, "Invalid Configuration", "Unable to confirm selection, invalid values found."
            )
        else:
            super().accept()
