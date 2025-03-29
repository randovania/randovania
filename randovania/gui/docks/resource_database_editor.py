from __future__ import annotations

import copy
import dataclasses
import functools
import json
import typing

from frozendict import frozendict
from PySide6 import QtCore, QtWidgets

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
from randovania.gui.lib.editable_table_model import AppendableEditableTableModel, FieldDefinition
from randovania.lib import frozen_lib

if typing.TYPE_CHECKING:
    from randovania.game_description.db.region_list import RegionList
    from randovania.game_description.resources.resource_database import ResourceDatabase


def encode_extra(qt_value: str) -> tuple[bool, typing.Any]:
    try:
        decoded = json.loads(qt_value)
        if isinstance(decoded, dict):
            return True, frozen_lib.wrap(decoded)
        return False, None
    except json.JSONDecodeError:
        return False, None


GENERIC_FIELDS: list[FieldDefinition] = [
    FieldDefinition[str, str]("Short Name", "short_name", from_qt=None),
    FieldDefinition[str, str]("Long Name", "long_name"),
    FieldDefinition[str, frozendict](
        "Extra", "extra", to_qt=lambda v: json.dumps(frozen_lib.unwrap(v)), from_qt=encode_extra
    ),
]


class ResourceDatabaseGenericModel(AppendableEditableTableModel[ResourceInfo]):
    """Model for editing a database of ResourceInfo using a QTableView"""

    def __init__(self, db: ResourceDatabase, resource_type: ResourceType):
        super().__init__()
        self.db = db
        self.resource_type = resource_type

    @typing.override
    def _all_columns(self) -> list[FieldDefinition]:
        return GENERIC_FIELDS

    @typing.override
    def _get_items(self) -> list[ResourceInfo]:
        return typing.cast("list[ResourceInfo]", self.db.get_by_type(self.resource_type))

    @typing.override
    def _create_item(self, short_name: str) -> ResourceInfo:
        return SimpleResourceInfo(self.db.first_unused_resource_index(), short_name, short_name, self.resource_type)

    @typing.override
    def _get_item_identifier(self, item: ResourceInfo) -> str:
        return item.short_name

    @typing.override
    def append_item(self, resource: ResourceInfo) -> bool:
        assert resource.resource_index == self.db.first_unused_resource_index()
        return super().append_item(resource)


ITEM_FIELDS = copy.copy(GENERIC_FIELDS)
ITEM_FIELDS.insert(2, FieldDefinition("Max Capacity", "max_capacity", from_qt=lambda v: (v > 0, v)))


class ResourceDatabaseItemModel(ResourceDatabaseGenericModel):
    """Model for editing a database of ItemResourceInfo using a QTableView"""

    def __init__(self, db: ResourceDatabase):
        super().__init__(db, ResourceType.ITEM)

    @typing.override
    def _all_columns(self) -> list[FieldDefinition]:
        return ITEM_FIELDS

    @typing.override
    def _create_item(self, short_name: str) -> ItemResourceInfo:
        return ItemResourceInfo(self.db.first_unused_resource_index(), short_name, short_name, 1)


TRICK_FIELDS = copy.copy(GENERIC_FIELDS)
TRICK_FIELDS.insert(2, FieldDefinition("Description", "description"))


class ResourceDatabaseTrickModel(ResourceDatabaseGenericModel):
    """Model for editing a database of TrickResourceInfo using a QTableView"""

    def __init__(self, db: ResourceDatabase):
        super().__init__(db, ResourceType.TRICK)

    @typing.override
    def _all_columns(self) -> list[FieldDefinition]:
        return TRICK_FIELDS

    @typing.override
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
            tab_model = tab.model()
            assert isinstance(tab_model, ResourceDatabaseGenericModel)
            tab.model().dataChanged.connect(functools.partial(self._on_data_changed, tab_model))

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
