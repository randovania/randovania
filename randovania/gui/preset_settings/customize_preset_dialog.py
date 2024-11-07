from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtGui, QtWidgets

from randovania.gui import game_specific_gui
from randovania.gui.generated.customize_preset_dialog_ui import Ui_CustomizePresetDialog
from randovania.gui.lib import common_qt_lib
from randovania.layout import filtered_database

if TYPE_CHECKING:
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.gui.preset_settings.preset_tab import PresetTab
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetTabRoot(QtWidgets.QWidget):
    tab_type: type[PresetTab]
    current_tab: PresetTab | None

    def __init__(self, owner: CustomizePresetDialog, tab_type: type[PresetTab]):
        super().__init__()
        self.owner = owner
        self.tab_type = tab_type
        self.current_tab = None

        self.root_layout = QtWidgets.QVBoxLayout(self)
        self.root_layout.setContentsMargins(0, 0, 0, 0)

    def showEvent(self, arg: QtGui.QShowEvent) -> None:
        if self.current_tab is None:
            editor = self.owner.editor
            self.current_tab = self.tab_type(
                editor,
                filtered_database.game_description_for_layout(editor.configuration),
                self.owner.window_manager,
            )
            self.root_layout.addWidget(self.current_tab)
            self.current_tab.on_preset_changed(editor.create_custom_preset_with())
            self.owner.set_visible_tab(self)
            self.current_tab.update_experimental_visibility()

        return super().showEvent(arg)

    def release_widget(self):
        self.current_tab.deleteLater()
        self.current_tab = None


class CustomizePresetDialog(QtWidgets.QDialog, Ui_CustomizePresetDialog):
    _editor: PresetEditor
    _current_tab: PresetTabRoot | None

    def __init__(self, window_manager: WindowManager, editor: PresetEditor):
        super().__init__()
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)

        self._editor = editor
        self.window_manager = window_manager
        _tab_types = list(game_specific_gui.preset_editor_tabs_for(editor, window_manager))
        self._current_tab = None
        self.item_to_widget = {}

        first_selection = None

        # Add entries
        for extra_tab in _tab_types:
            # Skip experimental if we don't have the setting on
            if not self.editor._options.experimental_settings and extra_tab.is_experimental():
                continue

            tab = PresetTabRoot(self, extra_tab)
            list_item = QtWidgets.QListWidgetItem(tab.tab_type.tab_title())

            self.item_to_widget[list_item.text()] = tab
            self.stackedWidget.addWidget(tab)

            # Add placeholder header entry, that gets proper text later
            if extra_tab.header_name():
                if self.listWidget.count() > 0:
                    seperator = QtWidgets.QListWidgetItem("")
                    seperator.setFlags(QtGui.Qt.ItemFlag.NoItemFlags)
                    self.listWidget.addItem(seperator)
                header = QtWidgets.QListWidgetItem(extra_tab.header_name())
                font = header.font()
                font.setBold(True)
                font.setPointSizeF(font.pointSize() * 1.2)
                header.setFont(font)
                header.setFlags(QtGui.Qt.ItemFlag.NoItemFlags)
                self.listWidget.addItem(header)

            self.listWidget.addItem(list_item)

            if first_selection is None:
                first_selection = list_item

        self.listWidget.setCurrentItem(first_selection)
        self.listWidget.currentItemChanged.connect(self.changed_list_item_selection)
        # Need some extra space to adjust for scrollbar
        self.listWidget.setMaximumWidth(self.listWidget.sizeHintForColumn(0) * 1.12)

        self.name_edit.textEdited.connect(self._edit_name)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def set_visible_tab(self, tab: PresetTabRoot):
        if tab != self._current_tab:
            if self._current_tab is not None:
                self._current_tab.release_widget()
            self._current_tab = tab

    def changed_list_item_selection(self, item: QtWidgets.QListWidgetItem):
        widget = self.item_to_widget[item.text()]
        self.stackedWidget.setCurrentWidget(widget)

    # Options
    def on_preset_changed(self, preset: Preset):
        common_qt_lib.set_edit_if_different(self.name_edit, preset.name)
        if (tab := self.current_preset_tab) is not None:
            tab.on_preset_changed(preset)

    def _edit_name(self, value: str):
        with self._editor as editor:
            editor.name = value

    @property
    def editor(self):
        return self._editor

    @property
    def current_preset_tab(self) -> PresetTab | None:
        if self._current_tab is not None:
            return self._current_tab.current_tab
        return None
