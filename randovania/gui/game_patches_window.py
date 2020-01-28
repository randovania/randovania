from PySide2.QtWidgets import QMainWindow, QComboBox

from randovania.gui.generated.game_patches_window_ui import Ui_GamePatchesWindow
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.patcher_configuration import PickupModelStyle, PickupModelDataSource
from randovania.layout.preset import Preset


class GamePatchesWindow(QMainWindow, Ui_GamePatchesWindow):
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

        # TODO: implement the LOCATION data source
        self.pickup_data_source_combo.removeItem(self.pickup_data_source_combo.findData(PickupModelDataSource.LOCATION))

        # Signals
        self.warp_to_start_check.stateChanged.connect(self._persist_option_then_notify("warp_to_start"))
        self.include_menu_mod_check.stateChanged.connect(self._persist_option_then_notify("include_menu_mod"))

        self.pickup_model_combo.currentIndexChanged.connect(self._persist_enum(self.pickup_model_combo,
                                                                               "pickup_model_style"))
        self.pickup_data_source_combo.currentIndexChanged.connect(self._persist_enum(self.pickup_data_source_combo,
                                                                                     "pickup_model_data_source"))

    def _persist_option_then_notify(self, attribute_name: str):
        def persist(value: int):
            with self._editor as options:
                setattr(options, attribute_name, bool(value))

        return persist

    def _persist_enum(self, combo: QComboBox, attribute_name: str):
        def persist(index: int):
            with self._editor as options:
                options.set_patcher_configuration_field(attribute_name, combo.itemData(index))

        return persist

    def on_preset_changed(self, preset: Preset):
        patcher_config = preset.patcher_configuration
        self.warp_to_start_check.setChecked(patcher_config.warp_to_start)
        self.include_menu_mod_check.setChecked(patcher_config.menu_mod)

        self.pickup_model_combo.setCurrentIndex(self.pickup_model_combo.findData(patcher_config.pickup_model_style))
        self.pickup_data_source_combo.setCurrentIndex(
            self.pickup_data_source_combo.findData(patcher_config.pickup_model_data_source))
        self.pickup_data_source_combo.setEnabled(patcher_config.pickup_model_style != PickupModelStyle.ALL_VISIBLE)
