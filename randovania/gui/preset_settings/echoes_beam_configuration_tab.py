import dataclasses
import functools

from PySide2 import QtWidgets
from PySide2.QtWidgets import QComboBox

from randovania.gui.generated.preset_echoes_beam_configuration_ui import Ui_PresetEchoesBeamConfiguration
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.prime2.beam_configuration import BeamAmmoConfiguration
from randovania.layout.preset import Preset

_BEAMS = {
    "power": "Power Beam",
    "dark": "Dark Beam",
    "light": "Light Beam",
    "annihilator": "Annihilator Beam",
}


class PresetEchoesBeamConfiguration(PresetTab, Ui_PresetEchoesBeamConfiguration):
    _editor: PresetEditor

    def __init__(self, editor: PresetEditor):
        super().__init__()
        self.setupUi(self)
        self._editor = editor

        def _add_header(text: str, col: int):
            label = QtWidgets.QLabel(self.beam_configuration_group)
            label.setText(text)
            self.beam_configuration_layout.addWidget(label, 0, col)

        _add_header("Ammo A", 1)
        _add_header("Ammo B", 2)
        _add_header("Uncharged", 3)
        _add_header("Charged", 4)
        _add_header("Combo", 5)
        _add_header("Missiles for Combo", 6)

        self._beam_ammo_a = {}
        self._beam_ammo_b = {}
        self._beam_uncharged = {}
        self._beam_charged = {}
        self._beam_combo = {}
        self._beam_missile = {}

        def _create_ammo_combo():
            combo = QComboBox(self.beam_configuration_group)
            combo.addItem("None", -1)
            combo.addItem("Power Bomb", 43)
            combo.addItem("Missile", 44)
            combo.addItem("Dark Ammo", 45)
            combo.addItem("Light Ammo", 46)
            return combo

        row = 1
        for beam, beam_name in _BEAMS.items():
            label = QtWidgets.QLabel(self.beam_configuration_group)
            label.setText(beam_name)
            self.beam_configuration_layout.addWidget(label, row, 0)

            ammo_a = _create_ammo_combo()
            ammo_a.currentIndexChanged.connect(functools.partial(
                self._on_ammo_type_combo_changed, beam, ammo_a, False))
            self._beam_ammo_a[beam] = ammo_a
            self.beam_configuration_layout.addWidget(ammo_a, row, 1)

            ammo_b = _create_ammo_combo()
            ammo_b.currentIndexChanged.connect(functools.partial(
                self._on_ammo_type_combo_changed, beam, ammo_b, True))
            self._beam_ammo_b[beam] = ammo_b
            self.beam_configuration_layout.addWidget(ammo_b, row, 2)

            spin_box = QtWidgets.QSpinBox(self.beam_configuration_group)
            spin_box.setSuffix(" ammo")
            spin_box.setMaximum(250)
            spin_box.valueChanged.connect(functools.partial(
                self._on_ammo_cost_spin_changed, beam, "uncharged_cost"
            ))
            self._beam_uncharged[beam] = spin_box
            self.beam_configuration_layout.addWidget(spin_box, row, 3)

            spin_box = QtWidgets.QSpinBox(self.beam_configuration_group)
            spin_box.setSuffix(" ammo")
            spin_box.setMaximum(250)
            spin_box.valueChanged.connect(functools.partial(
                self._on_ammo_cost_spin_changed, beam, "charged_cost"
            ))
            self._beam_charged[beam] = spin_box
            self.beam_configuration_layout.addWidget(spin_box, row, 4)

            spin_box = QtWidgets.QSpinBox(self.beam_configuration_group)
            spin_box.setSuffix(" ammo")
            spin_box.setMaximum(250)
            spin_box.valueChanged.connect(functools.partial(
                self._on_ammo_cost_spin_changed, beam, "combo_ammo_cost"
            ))
            self._beam_combo[beam] = spin_box
            self.beam_configuration_layout.addWidget(spin_box, row, 5)

            spin_box = QtWidgets.QSpinBox(self.beam_configuration_group)
            spin_box.setSuffix(" missile")
            spin_box.setMaximum(250)
            spin_box.setMinimum(1)
            spin_box.valueChanged.connect(functools.partial(
                self._on_ammo_cost_spin_changed, beam, "combo_missile_cost"
            ))
            self._beam_missile[beam] = spin_box
            self.beam_configuration_layout.addWidget(spin_box, row, 6)

            row += 1

    @property
    def uses_patches_tab(self) -> bool:
        return True

    def _on_ammo_type_combo_changed(self, beam: str, combo: QComboBox, is_ammo_b: bool, _):
        with self._editor as editor:
            beam_configuration = editor.configuration.beam_configuration
            old_config: BeamAmmoConfiguration = getattr(beam_configuration, beam)
            if is_ammo_b:
                new_config = dataclasses.replace(old_config, ammo_b=combo.currentData())
            else:
                new_config = dataclasses.replace(old_config, ammo_a=combo.currentData())

            editor.set_configuration_field("beam_configuration",
                                           dataclasses.replace(beam_configuration, **{beam: new_config}))

    def _on_ammo_cost_spin_changed(self, beam: str, field_name: str, value: int):
        with self._editor as editor:
            beam_configuration = editor.configuration.beam_configuration
            new_config = dataclasses.replace(getattr(beam_configuration, beam),
                                             **{field_name: value})
            editor.set_configuration_field("beam_configuration",
                                           dataclasses.replace(beam_configuration, **{beam: new_config}))

    def on_preset_changed(self, preset: Preset):
        beam_configuration = preset.configuration.beam_configuration

        for beam in _BEAMS:
            config: BeamAmmoConfiguration = getattr(beam_configuration, beam)

            self._beam_ammo_a[beam].setCurrentIndex(self._beam_ammo_a[beam].findData(config.ammo_a))
            self._beam_ammo_b[beam].setCurrentIndex(self._beam_ammo_b[beam].findData(config.ammo_b))
            self._beam_ammo_b[beam].setEnabled(config.ammo_a != -1)
            self._beam_uncharged[beam].setValue(config.uncharged_cost)
            self._beam_charged[beam].setValue(config.charged_cost)
            self._beam_combo[beam].setValue(config.combo_ammo_cost)
            self._beam_missile[beam].setValue(config.combo_missile_cost)
