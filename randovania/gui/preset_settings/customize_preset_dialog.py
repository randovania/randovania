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
        header_entry_counts = []

        index_for_headers = []
        # Maybe instead of hardcoding the headers like this, we have some kind of enum? Then we could also
        # change the presetTabs to instead of having "uses patches" to directly indicate which header they should be
        # displayed under. Future stuff tho.
        for header_name in [
            "Randomizer Logic",
            "Game Modifications",
            "Preset Info",
        ]:
            # Add headers
            header_entry = QtWidgets.QListWidgetItem(header_name)
            font = header_entry.font()
            font.setBold(True)
            font.setUnderline(True)
            font.setPointSizeF(font.pointSize() * 1.2)
            header_entry.setFont(font)
            header_entry.setFlags(QtGui.Qt.ItemFlag.NoItemFlags)
            self.listWidget.addItem(header_entry)
            index_for_headers.append(self.listWidget.count())
            header_entry_counts.append(0)

        first_selection = None
        # Add child tabs, will be positioned under their corresponding headers
        for extra_tab in _tab_types:
            if not self.editor._options.experimental_settings and extra_tab.is_experimental():
                continue

            tab = PresetTabRoot(self, extra_tab)
            list_item = QtWidgets.QListWidgetItem(tab.tab_type.tab_title())

            self.listToWidget[list_item.text()] = tab
            self.stackedWidget.addWidget(tab)
            if extra_tab.tab_title() == "Preset Description":
                index = 2
            elif extra_tab.uses_patches_tab():
                index = 1
            else:
                index = 0

            self.listWidget.insertItem(index_for_headers[index], list_item)
            header_entry_counts[index] += 1
            for i, indexAdjust in enumerate(index_for_headers):
                if i < index:
                    continue
                index_for_headers[i] += 1

            if first_selection is None:
                first_selection = list_item

        # Remove headers that don't have children.
        for index, count in zip(index_for_headers, header_entry_counts):
            if count == 0:
                self.listWidget.takeItem(index - 1)

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
