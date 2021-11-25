import copy
import dataclasses
import json
import typing

from PySide2 import QtWidgets, QtCore
from PySide2.QtCore import Qt
from frozendict import frozendict

from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceInfo
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.resources.trick_resource_info import TrickResourceInfo
from randovania.gui.generated.resource_database_editor_ui import Ui_ResourceDatabaseEditor
from randovania.gui.lib.common_qt_lib import set_default_window_icon


@dataclasses.dataclass(frozen=True)
class FieldDefinition:
    display_name: str
    field_name: str
    to_qt: typing.Callable[[typing.Any], typing.Any]
    from_qt: typing.Callable[[typing.Any], tuple[bool, typing.Any]]


def encode_extra(qt_value):
    try:
        decoded = json.loads(qt_value)
        if isinstance(decoded, dict):
            return True, frozendict(decoded)
    except json.JSONDecodeError:
        return False, None


GENERIC_FIELDS = [
    FieldDefinition("Short Name", "short_name", lambda v: v, lambda v: (True, v)),
    FieldDefinition("Long Name", "long_name", lambda v: v, lambda v: (True, v)),
    FieldDefinition("Extra", "extra", lambda v: json.dumps(v), encode_extra),
]


class ResourceDatabaseGenericModel(QtCore.QAbstractTableModel):
    def __init__(self, db: ResourceDatabase, resource_type: ResourceType):
        super().__init__()
        self.db = db
        self.resource_type = resource_type
        self.allow_edits = True

    def _get_items(self):
        return self.db.get_by_type(self.resource_type)

    def set_allow_edits(self, value: bool):
        self.beginResetModel()
        self.allow_edits = value
        self.endResetModel()

    def all_columns(self) -> list[FieldDefinition]:
        return GENERIC_FIELDS

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = ...) -> typing.Any:
        if role != Qt.DisplayRole:
            return None

        if orientation != Qt.Horizontal:
            return section

        return self.all_columns()[section].display_name

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        result = len(self._get_items())
        if self.allow_edits:
            result += 1
        return result

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self.all_columns())

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> typing.Any:
        if role not in {Qt.DisplayRole, Qt.EditRole}:
            return None

        all_items = self._get_items()
        if index.row() < len(all_items):
            resource = all_items[index.row()]
            field = self.all_columns()[index.column()]
            return field.to_qt(getattr(resource, field.field_name))

        elif role == Qt.DisplayRole:
            if index.column() == 0:
                return "New..."
        else:
            return ""

    def setData(self, index: QtCore.QModelIndex, value: typing.Any, role: int = ...) -> bool:
        if role == Qt.ItemDataRole.EditRole:
            all_items = self._get_items()
            if index.row() < len(all_items):
                resource = all_items[index.row()]
                field = self.all_columns()[index.column()]
                valid, new_value = field.from_qt(value)
                if valid:
                    all_items[index.row()] = dataclasses.replace(
                        resource, **{field.field_name: new_value},
                    )
                    self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])
                    return True
            else:
                if value:
                    return self.append_item(self._create_item(value))
        return False

    def _create_item(self, short_name) -> ResourceInfo:
        return SimpleResourceInfo(short_name, short_name, self.resource_type, frozendict())

    def append_item(self, resource: ResourceInfo) -> bool:
        row = self.rowCount()
        self.beginInsertRows(QtCore.QModelIndex(), row + 1, row + 1)
        self._get_items().append(resource)
        self.endInsertRows()
        return True

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlags:
        result = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        if self.allow_edits:
            if index.row() == len(self._get_items()):
                if index.column() == 0:
                    result |= QtCore.Qt.ItemIsEditable
            else:
                if index.column() > 0:
                    result |= QtCore.Qt.ItemIsEditable
        return result


ITEM_FIELDS = copy.copy(GENERIC_FIELDS)
ITEM_FIELDS.insert(2, FieldDefinition("Max Capacity", "max_capacity", lambda v: v, lambda v: (v > 0, v)))


class ResourceDatabaseItemModel(ResourceDatabaseGenericModel):
    def __init__(self, db: ResourceDatabase):
        super().__init__(db, ResourceType.ITEM)

    def all_columns(self):
        return ITEM_FIELDS

    def _create_item(self, short_name) -> ItemResourceInfo:
        return ItemResourceInfo(short_name, short_name, 1, frozendict())


TRICK_FIELDS = copy.copy(GENERIC_FIELDS)
TRICK_FIELDS.insert(2, FieldDefinition("Description", "description", lambda v: v, lambda v: (True, v)))


class ResourceDatabaseTrickModel(ResourceDatabaseGenericModel):
    def __init__(self, db: ResourceDatabase):
        super().__init__(db, ResourceType.TRICK)

    def all_columns(self):
        return TRICK_FIELDS

    def _create_item(self, short_name) -> TrickResourceInfo:
        return TrickResourceInfo(short_name, short_name, "", frozendict())


class ResourceDatabaseEditor(QtWidgets.QDockWidget, Ui_ResourceDatabaseEditor):
    def __init__(self, parent: QtWidgets.QWidget, db: ResourceDatabase):
        super().__init__(parent)
        self.setupUi(self)
        set_default_window_icon(self)

        self.db = db
        self.tab_item.setModel(ResourceDatabaseItemModel(db))
        self.tab_event.setModel(ResourceDatabaseGenericModel(db, ResourceType.EVENT))
        self.tab_trick.setModel(ResourceDatabaseTrickModel(db))
        self.tab_damage.setModel(ResourceDatabaseGenericModel(db, ResourceType.DAMAGE))
        self.tab_version.setModel(ResourceDatabaseGenericModel(db, ResourceType.VERSION))
        self.tab_misc.setModel(ResourceDatabaseGenericModel(db, ResourceType.MISC))

    def set_allow_edits(self, value: bool):
        for tab in [self.tab_item, self.tab_event, self.tab_trick, self.tab_damage,
                    self.tab_version, self.tab_misc]:
            tab.model().set_allow_edits(value)
