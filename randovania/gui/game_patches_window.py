from PySide2.QtWidgets import QMainWindow, QComboBox

from randovania.gui.background_task_mixin import BackgroundTaskMixin
from randovania.gui.game_patches_window_ui import Ui_GamePatchesWindow
from randovania.gui.tab_service import TabService
from randovania.interface_common.options import Options
from randovania.layout.patcher_configuration import PickupModelStyle, PickupModelDataSource


class GamePatchesWindow(QMainWindow, Ui_GamePatchesWindow):
    _options: Options

    def __init__(self, tab_service: TabService, background_processor: BackgroundTaskMixin, options: Options):
        super().__init__()
        self.setupUi(self)
        self._options = options

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

        self.varia_suit_spin_box.valueChanged.connect(self._persist_float("varia_suit_damage"))
        self.dark_suit_spin_box.valueChanged.connect(self._persist_float("dark_suit_damage"))

        self.pickup_model_combo.currentIndexChanged.connect(self._persist_enum(self.pickup_model_combo,
                                                                               "pickup_model_style"))
        self.pickup_data_source_combo.currentIndexChanged.connect(self._persist_enum(self.pickup_data_source_combo,
                                                                                     "pickup_model_data_source"))

    def _persist_option_then_notify(self, attribute_name: str):
        def persist(value: int):
            with self._options as options:
                setattr(options, attribute_name, bool(value))

        return persist

    def _persist_float(self, attribute_name: str):
        def persist(value: float):
            with self._options as options:
                options.set_patcher_configuration_field(attribute_name, value)

        return persist

    def _persist_enum(self, combo: QComboBox, attribute_name: str):
        def persist(index: int):
            with self._options as options:
                options.set_patcher_configuration_field(attribute_name, combo.itemData(index))

        return persist

    def on_options_changed(self, options: Options):
        self.warp_to_start_check.setChecked(options.warp_to_start)
        self.include_menu_mod_check.setChecked(options.include_menu_mod)

        self.varia_suit_spin_box.setValue(options.patcher_configuration.varia_suit_damage)
        self.dark_suit_spin_box.setValue(options.patcher_configuration.dark_suit_damage)

        self.pickup_model_combo.setCurrentIndex(self.pickup_model_combo.findData(options.pickup_model_style))
        self.pickup_data_source_combo.setCurrentIndex(
            self.pickup_data_source_combo.findData(options.pickup_model_data_source))
        self.pickup_data_source_combo.setEnabled(options.pickup_model_style != PickupModelStyle.ALL_VISIBLE)
