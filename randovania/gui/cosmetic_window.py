from PySide2.QtWidgets import QMainWindow

from randovania.gui.background_task_mixin import BackgroundTaskMixin
from randovania.gui.cosmetic_window_ui import Ui_CosmeticWindow
from randovania.gui.tab_service import TabService
from randovania.interface_common.options import Options


class CosmeticWindow(QMainWindow, Ui_CosmeticWindow):
    _options: Options

    def __init__(self, tab_service: TabService, background_processor: BackgroundTaskMixin, options: Options):
        super().__init__()
        self.setupUi(self)
        self._options = options

        # Signals
        self.remove_hud_popup_check.stateChanged.connect(self._persist_option_then_notify("hud_memo_popup_removal"))
        self.faster_credits_check.stateChanged.connect(self._persist_option_then_notify("speed_up_credits"))
        self.open_map_check.stateChanged.connect(self._persist_option_then_notify("open_map"))
        self.pickup_markers_check.stateChanged.connect(self._persist_option_then_notify("pickup_markers"))

    def _persist_option_then_notify(self, attribute_name: str):
        def persist(value: int):
            with self._options as options:
                setattr(options, attribute_name, bool(value))

        return persist

    def on_options_changed(self, options: Options):
        self.remove_hud_popup_check.setChecked(options.hud_memo_popup_removal)
        self.faster_credits_check.setChecked(options.speed_up_credits)
        self.open_map_check.setChecked(options.open_map)
        self.pickup_markers_check.setChecked(options.pickup_markers)
