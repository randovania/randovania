from PySide2.QtWidgets import QMainWindow

from randovania.gui.background_task_mixin import BackgroundTaskMixin
from randovania.gui.game_patches_window_ui import Ui_GamePatchesWindow
from randovania.gui.tab_service import TabService
from randovania.interface_common.options import Options


class GamePatchesWindow(QMainWindow, Ui_GamePatchesWindow):
    _options: Options

    def __init__(self, tab_service: TabService, background_processor: BackgroundTaskMixin, options: Options):
        super().__init__()
        self.setupUi(self)
        self._options = options

        # Signals
        self.warp_to_start_check.stateChanged.connect(self._persist_option_then_notify("warp_to_start"))
        self.include_menu_mod_check.stateChanged.connect(self._persist_option_then_notify("include_menu_mod"))

    def _persist_option_then_notify(self, attribute_name: str):
        def persist(value: int):
            with self._options as options:
                setattr(options, attribute_name, bool(value))

        return persist

    def on_options_changed(self):
        self.warp_to_start_check.setChecked(self._options.warp_to_start)
        self.include_menu_mod_check.setChecked(self._options.include_menu_mod)
