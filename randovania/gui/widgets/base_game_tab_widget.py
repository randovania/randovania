from PySide6 import QtWidgets, QtCore, QtGui

from randovania.games.game import RandovaniaGame
from randovania.gui.lib import faq_lib, hints_text
from randovania.gui.lib.background_task_mixin import BackgroundTaskMixin
from randovania.gui.lib.window_manager import WindowManager
from randovania.gui.widgets.generate_game_widget import GenerateGameWidget
from randovania.interface_common.options import Options


class BaseGameTabWidget(QtWidgets.QTabWidget):
    tab_intro: QtWidgets.QWidget
    tab_generate_game: GenerateGameWidget
    quick_generate_button: QtWidgets.QPushButton
    game_cover_label: QtWidgets.QLabel | None = None
    faq_label: QtWidgets.QLabel | None = None
    hint_item_names_tree_widget: QtWidgets.QTableWidget | None = None
    hint_locations_tree_widget: QtWidgets.QTreeWidget | None = None

    def __init__(self, window_manager: WindowManager, background_task: BackgroundTaskMixin, options: Options):
        super().__init__()
        self.setup_ui()
        self._window_manager = window_manager

        game = self.game()

        background_task.background_tasks_button_lock_signal.connect(self.enable_buttons_with_background_tasks)
        self.quick_generate_button.clicked.connect(self.on_quick_generate)

        return_button = QtWidgets.QPushButton("Back to games")
        return_button.clicked.connect(self._return_to_list)
        self.setCornerWidget(return_button, QtCore.Qt.Corner.TopLeftCorner)

        if self.game_cover_label is not None:
            self.game_cover_label.setPixmap(QtGui.QPixmap(game.data_path.joinpath('assets/cover.png').as_posix()))
            self.game_cover_label.setScaledContents(True)
            self.game_cover_label.setFixedSize(150, 200)

        if self.faq_label is not None:
            faq_lib.format_game_faq(game, self.faq_label)

        if self.hint_item_names_tree_widget is not None:
            hints_text.update_hints_text(game, self.hint_item_names_tree_widget)

        if self.hint_locations_tree_widget is not None:
            hints_text.update_hint_locations(game, self.hint_locations_tree_widget)

        self.tab_generate_game.setup_ui(game, window_manager, background_task, options)
        self._update_quick_generate_text()

    def setup_ui(self):
        raise NotImplementedError()

    @classmethod
    def game(cls) -> RandovaniaGame:
        raise NotImplementedError()
    
    def _update_quick_generate_text(self):
        preset_name = self.tab_generate_game.preset.name
        text = f"Quick Generate ({preset_name})"
        self.quick_generate_button.setText(text)

    def _return_to_list(self):
        self._window_manager.set_games_selector_visible(True)

    def on_options_changed(self, options: Options):
        self.tab_generate_game.on_options_changed(options)
        self._update_quick_generate_text()

    def on_quick_generate(self):
        self.tab_generate_game.generate_new_layout(spoiler=True)

    def enable_buttons_with_background_tasks(self, value: bool):
        self.quick_generate_button.setEnabled(value)
