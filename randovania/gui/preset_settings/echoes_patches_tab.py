from PySide2.QtWidgets import QComboBox

from randovania.gui.generated.preset_echoes_patches_ui import Ui_PresetEchoesPatches
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.pickup_model import PickupModelStyle, PickupModelDataSource
from randovania.layout.preset import Preset


class PresetEchoesPatches(PresetTab, Ui_PresetEchoesPatches):
    _editor: PresetEditor

    def __init__(self, editor: PresetEditor):
        super().__init__()
        self.setupUi(self)
        self._editor = editor

        # Item Data
        for i, value in enumerate(PickupModelStyle):
            self.pickup_model_combo.setItemData(i, value)

        for i, value in enumerate(PickupModelDataSource):
            self.pickup_data_source_combo.setItemData(i, value)

        self.include_menu_mod_label.setText(self.include_menu_mod_label.text().replace("color:#0000ff;", ""))

        # TODO: implement the LOCATION data source
        self.pickup_data_source_combo.removeItem(self.pickup_data_source_combo.findData(PickupModelDataSource.LOCATION))

        # Signals
        self.warp_to_start_check.stateChanged.connect(self._persist_option_then_notify("warp_to_start"))
        self.include_menu_mod_check.stateChanged.connect(self._persist_option_then_notify("include_menu_mod"))
        self.skip_final_bosses_check.stateChanged.connect(self._persist_option_then_notify("skip_final_bosses"))

        self.pickup_model_combo.currentIndexChanged.connect(self._persist_enum(self.pickup_model_combo,
                                                                               "pickup_model_style"))
        self.pickup_data_source_combo.currentIndexChanged.connect(self._persist_enum(self.pickup_data_source_combo,
                                                                                     "pickup_model_data_source"))

    @property
    def uses_patches_tab(self) -> bool:
        return True

    def _persist_option_then_notify(self, attribute_name: str):
        def persist(value: int):
            with self._editor as options:
                setattr(options, attribute_name, bool(value))

        return persist

    def _persist_enum(self, combo: QComboBox, attribute_name: str):
        def persist(index: int):
            with self._editor as options:
                options.set_configuration_field(attribute_name, combo.itemData(index))

        return persist

    def on_preset_changed(self, preset: Preset):
        config = preset.configuration
        self.warp_to_start_check.setChecked(config.warp_to_start)
        self.include_menu_mod_check.setChecked(config.menu_mod)
        self.skip_final_bosses_check.setChecked(config.skip_final_bosses)

        self.pickup_model_combo.setCurrentIndex(self.pickup_model_combo.findData(config.pickup_model_style))
        self.pickup_data_source_combo.setCurrentIndex(
            self.pickup_data_source_combo.findData(config.pickup_model_data_source))
        self.pickup_data_source_combo.setEnabled(config.pickup_model_style != PickupModelStyle.ALL_VISIBLE)
