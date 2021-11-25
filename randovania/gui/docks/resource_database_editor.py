import copy
import dataclasses
import json
import typing

from PySide2 import QtWidgets, QtCore
from PySide2.QtCore import Qt
from frozendict import frozendict

from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_type import ResourceType
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

    def _get_items(self):
        return self.db.get_by_type(self.resource_type)

    def all_columns(self) -> list[FieldDefinition]:
        return GENERIC_FIELDS

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = ...) -> typing.Any:
        if role != Qt.DisplayRole:
            return None

        if orientation != Qt.Horizontal:
            return section

        return self.all_columns()[section].display_name

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self._get_items())

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self.all_columns())

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> typing.Any:
        if role not in {Qt.DisplayRole, Qt.EditRole}:
            return None

        resource = self._get_items()[index.row()]
        field = self.all_columns()[index.column()]
        return field.to_qt(getattr(resource, field.field_name))

    def setData(self, index: QtCore.QModelIndex, value: typing.Any, role: int = ...) -> bool:
        if role == Qt.ItemDataRole.EditRole:
            resource = self._get_items()[index.row()]
            field = self.all_columns()[index.column()]
            valid, new_value = field.from_qt(value)
            if valid:
                self._get_items()[index.row()] = dataclasses.replace(
                    resource, **{field.field_name: new_value},
                )
                self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])
                return True
        return False

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlags:
        result = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
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


TRICK_FIELDS = copy.copy(GENERIC_FIELDS)
TRICK_FIELDS.insert(2, FieldDefinition("Description", "description", lambda v: v, lambda v: (True, v)))


class ResourceDatabaseTrickModel(ResourceDatabaseGenericModel):
    def __init__(self, db: ResourceDatabase):
        super().__init__(db, ResourceType.TRICK)

    def all_columns(self):
        return TRICK_FIELDS


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
