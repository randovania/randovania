import copy
import dataclasses
import functools
import json
import typing

from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import Qt

from randovania.game_description.requirements.base import Requirement
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceInfo
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.resources.trick_resource_info import TrickResourceInfo
from randovania.gui.dialog.connections_editor import ConnectionsEditor
from randovania.gui.generated.resource_database_editor_ui import Ui_ResourceDatabaseEditor
from randovania.gui.lib.common_qt_lib import set_default_window_icon
from randovania.gui.lib.connections_visualizer import ConnectionsVisualizer
from randovania.gui.lib.foldable import Foldable
from randovania.lib import frozen_lib


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
            return True, frozen_lib.wrap(decoded)
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
        return SimpleResourceInfo(self.db.first_unused_resource_index(), short_name, short_name, self.resource_type)

    def append_item(self, resource: ResourceInfo) -> bool:
        assert resource.resource_index == self.db.first_unused_resource_index()
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
        return ItemResourceInfo(self.db.first_unused_resource_index(), short_name, short_name, 1)


TRICK_FIELDS = copy.copy(GENERIC_FIELDS)
TRICK_FIELDS.insert(2, FieldDefinition("Description", "description", lambda v: v, lambda v: (True, v)))


class ResourceDatabaseTrickModel(ResourceDatabaseGenericModel):
    def __init__(self, db: ResourceDatabase):
        super().__init__(db, ResourceType.TRICK)

    def all_columns(self):
        return TRICK_FIELDS

    def _create_item(self, short_name) -> TrickResourceInfo:
        return TrickResourceInfo(self.db.first_unused_resource_index(), short_name, short_name, "")


@dataclasses.dataclass()
class TemplateEditor:
    template_name: str
    foldable: Foldable
    edit_button: QtWidgets.QPushButton
    template_layout: QtWidgets.QVBoxLayout
    visualizer: ConnectionsVisualizer | None
    connections_layout: QtWidgets.QGridLayout | None

    def create_visualizer(self, db: ResourceDatabase):
        for it in [self.connections_layout, self.visualizer]:
            if it is not None:
                it.deleteLater()

        self.connections_layout = QtWidgets.QGridLayout()
        self.template_layout.addLayout(self.connections_layout)

        self.connections_layout.setObjectName(f"connections_layout {self.template_name}")
        self.visualizer = ConnectionsVisualizer(
            self.foldable,
            self.connections_layout,
            db,
            db.requirement_template[self.template_name],
            False
        )


class ResourceDatabaseEditor(QtWidgets.QDockWidget, Ui_ResourceDatabaseEditor):
    editor_for_template: dict[str, TemplateEditor]

    ResourceChanged = QtCore.Signal(object)

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

        for tab in self._all_tabs:
            tab.model().dataChanged.connect(functools.partial(self._on_data_changed, tab.model()))

        self.editor_for_template = {}
        for name in db.requirement_template.keys():
            self.create_template_editor(name)

        self.create_new_template_button = QtWidgets.QPushButton()
        self.create_new_template_button.setText("Create new")
        self.create_new_template_button.clicked.connect(self.create_new_template)
        self.tab_template_layout.addWidget(self.create_new_template_button)

    @property
    def _all_tabs(self):
        return [self.tab_item, self.tab_event, self.tab_trick, self.tab_damage,
                self.tab_version, self.tab_misc]

    def _on_data_changed(self, model: ResourceDatabaseGenericModel, top_left: QtCore.QModelIndex,
                         bottom_right: QtCore.QModelIndex, roles):
        first_row = top_left.row()
        last_row = bottom_right.row()
        if first_row == last_row:
            self.ResourceChanged.emit(self.db.get_by_type(model.resource_type)[first_row])

    def set_allow_edits(self, value: bool):
        for tab in self._all_tabs:
            tab.model().set_allow_edits(value)

        self.create_new_template_button.setVisible(value)
        for editor in self.editor_for_template.values():
            editor.edit_button.setVisible(value)

    def create_new_template(self):
        template_name, did_confirm = QtWidgets.QInputDialog.getText(self, "New Template", "Insert template name:")
        if not did_confirm or template_name == "":
            return

        self.db.requirement_template[template_name] = Requirement.trivial()
        self.create_template_editor(template_name)
        self.tab_template_layout.removeWidget(self.create_new_template_button)
        self.tab_template_layout.addWidget(self.create_new_template_button)

    def create_template_editor(self, name: str):
        template_box = Foldable(name)
        template_box.setObjectName(f"template_box {name}")
        template_layout = QtWidgets.QVBoxLayout()
        template_layout.setObjectName(f"template_layout {name}")
        template_box.set_content_layout(template_layout)

        edit_template_button = QtWidgets.QPushButton()
        edit_template_button.setText("Edit")
        edit_template_button.clicked.connect(functools.partial(self.edit_template, name))
        template_layout.addWidget(edit_template_button)

        self.editor_for_template[name] = TemplateEditor(
            template_name=name,
            foldable=template_box,
            edit_button=edit_template_button,
            template_layout=template_layout,
            visualizer=None,
            connections_layout=None,
        )
        self.editor_for_template[name].create_visualizer(self.db)

        self.tab_template_layout.addWidget(template_box)

    def edit_template(self, name: str):
        requirement = self.db.requirement_template[name]
        editor = ConnectionsEditor(self, self.db, requirement)
        result = editor.exec_()
        if result == QtWidgets.QDialog.Accepted:
            self.db.requirement_template[name] = editor.final_requirement
            self.editor_for_template[name].create_visualizer(self.db)
