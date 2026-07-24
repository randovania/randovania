from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any, cast

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLayout,
    QLineEdit,
    QSpinBox,
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
from randovania.gui.lib.signal_handling import set_combo_with_value
from randovania.gui.widgets.scroll_protected import ScrollProtectedComboBox
from randovania.layout.base.trick_level import LayoutTrickLevel
from randovania.lib.enum_lib import iterate_enum

from .model import ROLE


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
        """Populate editor widgets with requirement data without emitting signals"""
        raise NotImplementedError

    def requirement(self) -> Requirement:
        """Assemble a new requirement with current widget selections"""
        raise NotImplementedError

    def widget(self) -> QWidget:
        """Returns the root widget used by the Editor"""
        return self._widget

    def name(self) -> str:
        """Returns the user-facing name for the Editor"""
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
        resource_info: ResourceInfo = self._combo_name.currentData(ROLE)
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
        return self._make_requirement(self._spinbox_amount.value(), self._combo_negate.currentData(ROLE))


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
        return self._make_requirement(self._combo_difficulty.currentData(ROLE).as_number, False)


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
        name: str = self.to_string(self._combo_name.currentData(ROLE))
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
        self._combo_area.currentTextChanged.connect(self._area_changed)
        self._combo_node.currentTextChanged.connect(self._notify_changed)

    def to_string(self, data: Region | Area | Node) -> str:
        return data.name

    def _repopulate_combo(self, combo: QComboBox, data: list[Any]) -> None:
        combo.clear()
        for item in data:
            combo.addItem(self.to_string(item), item)

    def populate(self, requirement: Requirement) -> None:
        requirement = cast(NodeRequirement, requirement)
        region: Region = self._region_list.region_with_name(requirement.node_identifier.region)
        area: Area = region.area_by_identifier(requirement.node_identifier.area_identifier)
        node: Node = self._region_list.node_by_identifier(requirement.node_identifier)

        with signals_blocked(self._combo_region):
            set_combo_with_value(self._combo_region, region)

        with signals_blocked(self._combo_area):
            self._repopulate_combo(self._combo_area, region.areas)
            set_combo_with_value(self._combo_area, area)

        with signals_blocked(self._combo_node):
            self._repopulate_combo(self._combo_node, area.nodes)
            set_combo_with_value(self._combo_node, node)

    def _region_changed(self, idx: int = -1) -> None:
        region: Region = self._combo_region.currentData(ROLE)
        with signals_blocked(self._combo_area):
            self._repopulate_combo(self._combo_area, region.areas)
        area: Area = next(iter(region.areas))
        set_combo_with_value(self._combo_area, area)
        self._area_changed()

    def _area_changed(self, text: str = "") -> None:
        area: Area = self._combo_area.currentData(ROLE)
        with signals_blocked(self._combo_node):
            self._repopulate_combo(self._combo_node, area.nodes)
        node: Node = next(iter(area.nodes))
        set_combo_with_value(self._combo_node, node)
        self._notify_changed()

    def requirement(self) -> NodeRequirement:
        node_identifier = NodeIdentifier(
            self.to_string(self._combo_region.currentData(ROLE)),
            self.to_string(self._combo_area.currentData(ROLE)),
            self.to_string(self._combo_node.currentData(ROLE)),
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
        _type: type = self._combo_type.currentData(ROLE)
        text: str = self._line_edit_comment.text()
        comment: str | None = text if len(text) > 0 else None
        return _type([], comment)


@contextmanager
def signals_blocked(widget: QWidget) -> Iterator[None]:
    previous = widget.signalsBlocked()
    widget.blockSignals(True)
    yield
    widget.blockSignals(previous)
