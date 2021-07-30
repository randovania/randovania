import functools

from PySide2 import QtWidgets, QtCore
from PySide2.QtWidgets import QComboBox

import randovania.games.patchers.claris_patcher
from randovania.game_description.resources.translator_gate import TranslatorGate
from randovania.gui.generated.preset_echoes_translators_ui import Ui_PresetEchoesTranslators
from randovania.gui.lib.common_qt_lib import set_combo_with_value
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.lib.enum_lib import iterate_enum
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.preset import Preset
from randovania.layout.prime2.translator_configuration import LayoutTranslatorRequirement


class PresetEchoesTranslators(PresetTab, Ui_PresetEchoesTranslators):
    _editor: PresetEditor

    def __init__(self, editor: PresetEditor):
        super().__init__()
        self.setupUi(self)
        self._editor = editor

        randomizer_data = randovania.games.patchers.claris_patcher.decode_randomizer_data()

        self.translators_layout.setAlignment(QtCore.Qt.AlignTop)
        self.translator_randomize_all_button.clicked.connect(self._on_randomize_all_gates_pressed)
        self.translator_randomize_all_with_unlocked_button.clicked.connect(self._on_randomize_all_gates_with_unlocked_pressed)
        self.translator_vanilla_actual_button.clicked.connect(self._on_vanilla_actual_gates_pressed)
        self.translator_vanilla_colors_button.clicked.connect(self._on_vanilla_colors_gates_pressed)

        self._combo_for_gate = {}

        for i, gate in enumerate(randomizer_data["TranslatorLocationData"]):
            label = QtWidgets.QLabel(self.translators_scroll_contents)
            label.setText(gate["Name"])
            self.translators_layout.addWidget(label, 3 + i, 0, 1, 1)

            combo = QComboBox(self.translators_scroll_contents)
            combo.gate = TranslatorGate(gate["Index"])
            for item in iterate_enum(LayoutTranslatorRequirement):
                combo.addItem(item.long_name, item)
            combo.currentIndexChanged.connect(functools.partial(self._on_gate_combo_box_changed, combo))

            self.translators_layout.addWidget(combo, 3 + i, 1, 1, 2)
            self._combo_for_gate[combo.gate] = combo

    @property
    def uses_patches_tab(self) -> bool:
        return True

    def _on_randomize_all_gates_pressed(self):
        with self._editor as editor:
            editor.set_configuration_field(
                "translator_configuration",
                editor.configuration.translator_configuration.with_full_random())

    def _on_randomize_all_gates_with_unlocked_pressed(self):
        with self._editor as editor:
            editor.set_configuration_field(
                "translator_configuration",
                editor.configuration.translator_configuration.with_full_random_with_unlocked())

    def _on_vanilla_actual_gates_pressed(self):
        with self._editor as editor:
            editor.set_configuration_field(
                "translator_configuration",
                editor.configuration.translator_configuration.with_vanilla_actual())

    def _on_vanilla_colors_gates_pressed(self):
        with self._editor as editor:
            editor.set_configuration_field(
                "translator_configuration",
                editor.configuration.translator_configuration.with_vanilla_colors())

    def _on_gate_combo_box_changed(self, combo: QComboBox, new_index: int):
        with self._editor as editor:
            editor.set_configuration_field(
                "translator_configuration",
                editor.configuration.translator_configuration.replace_requirement_for_gate(
                    combo.gate, combo.currentData()))

    def on_preset_changed(self, preset: Preset):
        translator_configuration = preset.configuration.translator_configuration
        for gate, combo in self._combo_for_gate.items():
            set_combo_with_value(combo, translator_configuration.translator_requirement[gate])
