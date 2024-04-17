from __future__ import annotations

import copy
import dataclasses
import functools
import json
import typing

from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt

from randovania.game_description.requirements.base import Requirement
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.resource_database import NamedRequirementTemplate
from randovania.game_description.resources.resource_info import ResourceInfo
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.resources.trick_resource_info import TrickResourceInfo
from randovania.gui.dialog.connections_editor import ConnectionsEditor
from randovania.gui.generated.resource_database_editor_ui import Ui_ResourceDatabaseEditor
from randovania.gui.lib.common_qt_lib import set_default_window_icon
from randovania.gui.lib.connections_visualizer import create_tree_items_for_requirement
from randovania.lib import frozen_lib

if typing.TYPE_CHECKING:
    from types import EllipsisType

    from randovania.game_description.db.region_list import RegionList
    from randovania.game_description.resources.resource_database import ResourceDatabase


@dataclasses.dataclass(frozen=True)
class FieldDefinition:
    display_name: str
    field_name: str
    to_qt: typing.Callable[[typing.Any], typing.Any]
    from_qt: typing.Callable[[typing.Any], tuple[bool, typing.Any]]


def encode_extra(qt_value: str) -> tuple[bool, typing.Any]:
    try:
        decoded = json.loads(qt_value)
        if isinstance(decoded, dict):
            return True, frozen_lib.wrap(decoded)
        return False, None
    except json.JSONDecodeError:
        return False, None


GENERIC_FIELDS = [
    FieldDefinition("Short Name", "short_name", lambda v: v, lambda v: (True, v)),
    FieldDefinition("Long Name", "long_name", lambda v: v, lambda v: (True, v)),
    FieldDefinition("Extra", "extra", lambda v: json.dumps(frozen_lib.unwrap(v)), encode_extra),
]


class ResourceDatabaseGenericModel(QtCore.QAbstractTableModel):
    def __init__(self, db: ResourceDatabase, resource_type: ResourceType):
        super().__init__()
        self.db = db
        self.resource_type = resource_type
        self.allow_edits = True

    def _get_items(self) -> list[ResourceInfo]:
        return typing.cast(list[ResourceInfo], self.db.get_by_type(self.resource_type))

    def set_allow_edits(self, value: bool) -> None:
        self.beginResetModel()
        self.allow_edits = value
        self.endResetModel()

    def all_columns(self) -> list[FieldDefinition]:
        return GENERIC_FIELDS

    def headerData(
        self, section: int, orientation: QtCore.Qt.Orientation, role: int | EllipsisType = ...
    ) -> typing.Any:
        if role != Qt.ItemDataRole.DisplayRole:
            return None

        if orientation != Qt.Orientation.Horizontal:
            return section

        return self.all_columns()[section].display_name

    def rowCount(self, parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex | EllipsisType = ...) -> int:
        result = len(self._get_items())
        if self.allow_edits:
            result += 1
        return result

    def columnCount(self, parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex | EllipsisType = ...) -> int:
        return len(self.all_columns())

    def data(
        self, index: QtCore.QModelIndex | QtCore.QPersistentModelIndex, role: int | EllipsisType = ...
    ) -> typing.Any:
        if role not in {Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole}:
            return None

        all_items = self._get_items()
        if index.row() < len(all_items):
            resource = all_items[index.row()]
            field = self.all_columns()[index.column()]
            return field.to_qt(getattr(resource, field.field_name))

        elif role == Qt.ItemDataRole.DisplayRole:
            if index.column() == 0:
                return "New..."
        else:
            return ""

    def setData(
        self,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
        value: typing.Any,
        role: int | EllipsisType = ...,
    ) -> bool:
        if role == Qt.ItemDataRole.EditRole:
            all_items = self._get_items()
            if index.row() < len(all_items):
                resource: ResourceInfo = all_items[index.row()]
                field = self.all_columns()[index.column()]
                valid, new_value = field.from_qt(value)
                if valid:
                    all_items[index.row()] = dataclasses.replace(
                        resource,
                        **{field.field_name: new_value},
                    )
                    self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])
                    return True
            else:
                if value:
                    all_items = self._get_items()
                    if any(item.short_name == value for item in all_items):
                        return False
                    return self.append_item(self._create_item(value))
        return False

    def _create_item(self, short_name: str) -> ResourceInfo:
        return SimpleResourceInfo(self.db.first_unused_resource_index(), short_name, short_name, self.resource_type)

    def append_item(self, resource: ResourceInfo) -> bool:
        assert resource.resource_index == self.db.first_unused_resource_index()
        row = self.rowCount()
        self.beginInsertRows(QtCore.QModelIndex(), row + 1, row + 1)
        self._get_items().append(resource)
        self.endInsertRows()
        return True

    def flags(self, index: QtCore.QModelIndex | QtCore.QPersistentModelIndex) -> QtCore.Qt.ItemFlag:
        result = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if self.allow_edits:
            if index.row() == len(self._get_items()):
                if index.column() == 0:
                    result |= Qt.ItemFlag.ItemIsEditable
            else:
                if index.column() > 0:
                    result |= Qt.ItemFlag.ItemIsEditable
        return result


ITEM_FIELDS = copy.copy(GENERIC_FIELDS)
ITEM_FIELDS.insert(2, FieldDefinition("Max Capacity", "max_capacity", lambda v: v, lambda v: (v > 0, v)))


class ResourceDatabaseItemModel(ResourceDatabaseGenericModel):
    def __init__(self, db: ResourceDatabase):
        super().__init__(db, ResourceType.ITEM)

    def all_columns(self) -> list[FieldDefinition]:
        return ITEM_FIELDS

    def _create_item(self, short_name: str) -> ItemResourceInfo:
        return ItemResourceInfo(self.db.first_unused_resource_index(), short_name, short_name, 1)


TRICK_FIELDS = copy.copy(GENERIC_FIELDS)
TRICK_FIELDS.insert(2, FieldDefinition("Description", "description", lambda v: v, lambda v: (True, v)))


class ResourceDatabaseTrickModel(ResourceDatabaseGenericModel):
    def __init__(self, db: ResourceDatabase):
        super().__init__(db, ResourceType.TRICK)

    def all_columns(self) -> list[FieldDefinition]:
        return TRICK_FIELDS

    def _create_item(self, short_name: str) -> TrickResourceInfo:
        return TrickResourceInfo(self.db.first_unused_resource_index(), short_name, short_name, "")


@dataclasses.dataclass()
class TemplateEditor:
    edit_item: QtWidgets.QTreeWidgetItem
    root_item: QtWidgets.QTreeWidgetItem
    connections_item: QtWidgets.QTreeWidgetItem | None = None

    def create_connections(
        self, tree: QtWidgets.QTreeWidget, requirement: Requirement, resource_database: ResourceDatabase
    ) -> None:
        if self.connections_item is not None:
            self.root_item.removeChild(self.connections_item)

        self.connections_item = create_tree_items_for_requirement(
            tree,
            self.root_item,
            requirement,
            resource_database,
        )


class ResourceDatabaseEditor(QtWidgets.QDockWidget, Ui_ResourceDatabaseEditor):
    editor_for_template: dict[str, TemplateEditor]

    ResourceChanged = QtCore.Signal(object)

    def __init__(self, parent: QtWidgets.QWidget, db: ResourceDatabase, region_list: RegionList):
        super().__init__(parent)
        self.setupUi(self)
        set_default_window_icon(self)

        self.db = db
        self.region_list = region_list
        self.tab_item.setModel(ResourceDatabaseItemModel(db))
        self.tab_event.setModel(ResourceDatabaseGenericModel(db, ResourceType.EVENT))
        self.tab_trick.setModel(ResourceDatabaseTrickModel(db))
        self.tab_damage.setModel(ResourceDatabaseGenericModel(db, ResourceType.DAMAGE))
        self.tab_version.setModel(ResourceDatabaseGenericModel(db, ResourceType.VERSION))
        self.tab_misc.setModel(ResourceDatabaseGenericModel(db, ResourceType.MISC))

        for tab in self._all_tabs:
            tab.model().dataChanged.connect(functools.partial(self._on_data_changed, tab.model()))

        self.tab_template.header().setVisible(False)
        self.create_new_template_item = QtWidgets.QTreeWidgetItem(self.tab_template)
        self.create_new_template_button = QtWidgets.QPushButton()
        self.create_new_template_button.setText("Create new")
        self.create_new_template_button.clicked.connect(self.create_new_template)
        self.tab_template.setItemWidget(self.create_new_template_item, 0, self.create_new_template_button)

        self.editor_for_template = {}
        for name in db.requirement_template.keys():
            self.create_template_editor(name)

    @property
    def _all_tabs(self) -> list[QtWidgets.QTableView]:
        return [self.tab_item, self.tab_event, self.tab_trick, self.tab_damage, self.tab_version, self.tab_misc]

    def _on_data_changed(
        self,
        model: ResourceDatabaseGenericModel,
        top_left: QtCore.QModelIndex,
        bottom_right: QtCore.QModelIndex,
        roles: None,
    ) -> None:
        first_row = top_left.row()
        last_row = bottom_right.row()
        if first_row == last_row:
            self.ResourceChanged.emit(self.db.get_by_type(model.resource_type)[first_row])

    def set_allow_edits(self, value: bool) -> None:
        for tab in self._all_tabs:
            tab_model = tab.model()
            assert isinstance(tab_model, ResourceDatabaseGenericModel)
            tab_model.set_allow_edits(value)

        self.create_new_template_item.setHidden(not value)
        for editor in self.editor_for_template.values():
            editor.edit_item.setHidden(not value)

    def create_new_template(self) -> None:
        template_name, did_confirm = QtWidgets.QInputDialog.getText(self, "New Template", "Insert template name:")
        if not did_confirm or template_name == "":
            return

        self.db.requirement_template[template_name] = NamedRequirementTemplate(template_name, Requirement.trivial())
        self.create_template_editor(template_name).setExpanded(True)

    def create_template_editor(self, name: str) -> QtWidgets.QTreeWidgetItem:
        template = self.db.requirement_template[name]
        item = QtWidgets.QTreeWidgetItem(self.tab_template)
        item.setText(0, template.display_name)

        rename_template_item = QtWidgets.QTreeWidgetItem(item)
        rename_template_edit = QtWidgets.QLineEdit(template.display_name)
        rename_template_edit.textChanged.connect(functools.partial(self.rename_template, name))
        self.tab_template.setItemWidget(rename_template_item, 0, rename_template_edit)

        edit_template_item = QtWidgets.QTreeWidgetItem(item)
        edit_template_button = QtWidgets.QPushButton()
        edit_template_button.setText("Edit")
        edit_template_button.clicked.connect(functools.partial(self.edit_template, name))
        self.tab_template.setItemWidget(edit_template_item, 0, edit_template_button)

        self.editor_for_template[name] = TemplateEditor(
            edit_template_item,
            item,
        )
        self.editor_for_template[name].create_connections(
            self.tab_template,
            template.requirement,
            self.db,
        )

        return item

    def rename_template(self, name: str, display_name: str) -> None:
        self.db.requirement_template[name] = dataclasses.replace(
            self.db.requirement_template[name], display_name=display_name
        )
        self.editor_for_template[name].root_item.setText(0, display_name)

    def edit_template(self, name: str) -> None:
        template = self.db.requirement_template[name]
        editor = ConnectionsEditor(self, self.db, self.region_list, template.requirement)
        result = editor.exec_()
        if result == QtWidgets.QDialog.DialogCode.Accepted:
            final_req = editor.final_requirement
            if final_req is None:
                return

            self.db.requirement_template[name] = dataclasses.replace(
                self.db.requirement_template[name],
                requirement=final_req,
            )
            self.editor_for_template[name].create_connections(
                self.tab_template,
                self.db.requirement_template[name].requirement,
                self.db,
            )
