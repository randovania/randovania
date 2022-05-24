from PySide6 import QtWidgets
from PySide6.QtCore import Signal
from qasync import asyncSlot

from randovania.game_description.game_description import GameDescription
from randovania.game_description.resources.trick_resource_info import TrickResourceInfo
from randovania.gui.lib import file_prompts, async_dialog, signal_handling
from randovania.gui.lib.common_qt_lib import set_default_window_icon
from randovania.gui.lib.scroll_protected import ScrollProtectedComboBox
from randovania.layout.base.trick_level import LayoutTrickLevel
from randovania.layout.versioned_preset import VersionedPreset
from randovania.lib import enum_lib


class ConnectionLayerWidget(QtWidgets.QDockWidget):
    FiltersUpdated = Signal()

    def __init__(self, parent: QtWidgets.QWidget, game: GameDescription):
        super().__init__(parent)
        set_default_window_icon(self)
        self.setWindowTitle("Layers")

        self.root_widget = QtWidgets.QScrollArea()
        self.root_layout = QtWidgets.QVBoxLayout(self.root_widget)
        self.root_widget.setWidgetResizable(True)
        self.setWidget(self.root_widget)

        self.contents_widget = QtWidgets.QWidget()
        self.contents_layout = QtWidgets.QVBoxLayout(self.contents_widget)
        self.root_widget.setWidget(self.contents_widget)

        self.title_label = QtWidgets.QLabel(self.contents_widget)
        self.title_label.setText("Select visible layers")
        self.contents_layout.addWidget(self.title_label)

        self.layer_checks = []
        for layer in game.layers:
            self.layer_checks.append(layer_check := QtWidgets.QCheckBox(self.contents_widget))
            layer_check.setText(layer)
            layer_check.setChecked(True)
            signal_handling.on_checked(layer_check, lambda it: self._notify_change())
            self.contents_layout.addWidget(layer_check)

        self.add_layer_button = QtWidgets.QPushButton(self.contents_widget)
        self.add_layer_button.setText("Add new layer")
        self.add_layer_button.setEnabled(False)
        self.add_layer_button.setToolTip("Not implemented")
        self.contents_layout.addWidget(self.add_layer_button)

        self.tricks_box = QtWidgets.QGroupBox(self.contents_widget)
        self.tricks_box.setTitle("Simplify connections with:")
        self.contents_layout.addWidget(self.tricks_box)
        self.tricks_layout = QtWidgets.QVBoxLayout(self.tricks_box)

        self.tricks = {}
        for trick in sorted(game.resource_database.trick, key=lambda it: it.long_name):
            trick_layout = QtWidgets.QHBoxLayout()
            self.tricks_layout.addLayout(trick_layout)

            trick_check = QtWidgets.QCheckBox(self.tricks_box)
            trick_check.setText(trick.long_name)
            trick_layout.addWidget(trick_check)

            trick_combo = ScrollProtectedComboBox(self.tricks_box)
            trick_layout.addWidget(trick_combo)
            for trick_level in enum_lib.iterate_enum(LayoutTrickLevel):
                trick_combo.addItem(trick_level.long_name, userData=trick_level.as_number)
            signal_handling.on_combo(trick_combo, lambda it: self._notify_change())
            trick_combo.setEnabled(False)

            signal_handling.on_checked(trick_check, trick_combo.setEnabled)
            signal_handling.on_checked(trick_check, lambda it: self._notify_change())

            self.tricks[(trick, trick_check)] = trick_combo

        self.load_preset_button = QtWidgets.QPushButton(self.contents_widget)
        self.load_preset_button.setText("Configure with preset")
        self.load_preset_button.clicked.connect(self._on_load_preset_slot)
        self.contents_layout.addWidget(self.load_preset_button)

        self.vertical_spacer = QtWidgets.QSpacerItem(20, 30, QtWidgets.QSizePolicy.Minimum,
                                                     QtWidgets.QSizePolicy.Expanding)
        self.contents_layout.addItem(self.vertical_spacer)

    def set_edit_mode(self, edit_mode: bool):
        for layer_check in self.layer_checks:
            layer_check.setEnabled(not edit_mode and layer_check.text() != "default")
            if edit_mode:
                layer_check.setChecked(True)

        self.add_layer_button.setVisible(edit_mode)
        self.tricks_box.setVisible(not edit_mode)
        self.load_preset_button.setVisible(not edit_mode)

    @asyncSlot()
    async def _on_load_preset_slot(self):
        await self._on_load_preset()

    async def _on_load_preset(self):
        preset_file = await file_prompts.prompt_preset(self, False)
        if preset_file is None:
            return

        try:
            preset = (await VersionedPreset.from_file(preset_file)).get_preset()

        except Exception as e:
            return await async_dialog.warning(
                self, "Invalid preset",
                f"Unable to load a preset from {preset_file}: {e}"
            )

        active_layers = preset.configuration.active_layers()
        for layer_check in self.layer_checks:
            layer_check.setChecked(layer_check.text() in active_layers)

        trick_level = preset.configuration.trick_level
        for (trick, trick_check), combo in self.tricks.items():
            trick_check.setChecked(trick_level.has_specific_level_for_trick(trick))
            idx = combo.findData(trick_level.level_for_trick(trick).as_number)
            combo.setCurrentIndex(idx)

    def selected_tricks(self) -> dict[TrickResourceInfo, int]:
        return {
            trick: combo.currentData()
            for (trick, trick_check), combo in self.tricks.items()
            if trick_check.isChecked()
        }

    def selected_layers(self) -> set[str]:
        return {
            layer_check.text()
            for layer_check in self.layer_checks
            if layer_check.isChecked()
        }

    def _notify_change(self):
        self.FiltersUpdated.emit()
