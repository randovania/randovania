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
        self.listToWidget = {}

        header_indices = []
        max_title_characters = 0

        first_selection = None
        # Add child tabs, will be positioned under their corresponding headers
        for extra_tab in _tab_types:
            if not self.editor._options.experimental_settings and extra_tab.is_experimental():
                continue

            tab = PresetTabRoot(self, extra_tab)
            list_item = QtWidgets.QListWidgetItem(tab.tab_type.tab_title())

            self.listToWidget[list_item.text()] = tab
            self.stackedWidget.addWidget(tab)

            if extra_tab.starts_new_header():
                header_indices.append(self.listWidget.count())
                seperator = QtWidgets.QListWidgetItem("")
                seperator.setFlags(QtGui.Qt.ItemFlag.NoItemFlags)
                self.listWidget.addItem(seperator)

            self.listWidget.addItem(list_item)

            if len(extra_tab.tab_title()) > max_title_characters:
                max_title_characters = len(extra_tab.tab_title())

            if first_selection is None:
                first_selection = list_item

        # Change seperator placeholders to have proper text
        for index in header_indices:
            self.listWidget.item(index).setText("─" * max_title_characters)

        self.listWidget.setCurrentItem(first_selection)
        self.listWidget.currentItemChanged.connect(self.changed_list_item_selection)
        self.listWidget.setMaximumWidth(self.listWidget.sizeHintForColumn(0) * 1.1)

        self.name_edit.textEdited.connect(self._edit_name)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def set_visible_tab(self, tab: PresetTabRoot):
        if tab != self._current_tab:
            if self._current_tab is not None:
                self._current_tab.release_widget()
            self._current_tab = tab

    def changed_list_item_selection(self, item: QtWidgets.QListWidgetItem):
        widget = self.listToWidget[item.text()]
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
