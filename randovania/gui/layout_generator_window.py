from typing import Dict

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMainWindow

from randovania.games.prime import binary_data
from randovania.gui.common_qt_lib import application_options, persist_bool_option
from randovania.gui.layout_generator_window_ui import Ui_LayoutGeneratorWindow
from randovania.resolver.data_reader import read_resource_database
from randovania.resolver.resources import SimpleResourceInfo


class LayoutGeneratorWindow(QMainWindow, Ui_LayoutGeneratorWindow):
    def __init__(self, main_window):
        super().__init__()
        self.setupUi(self)
        self._on_bulk_change = False

        data = binary_data.decode_default_prime2()
        self.resource_database = read_resource_database(data["resource_database"])

        options = application_options()

        # Difficulty
        self.minimumDifficulty.setValue(options.minimum_difficulty)
        self.maximumDifficulty.setValue(options.maximum_difficulty)
        self.minimumDifficulty.valueChanged.connect(self.on_min_difficulty_changed)
        self.maximumDifficulty.valueChanged.connect(self.on_max_difficulty_changed)

        # Checkers
        self.remove_item_loss.setChecked(options.remove_item_loss)
        self.remove_item_loss.stateChanged.connect(persist_bool_option("remove_item_loss"))
        self.randomize_elevators.setChecked(options.randomize_elevators)
        self.randomize_elevators.stateChanged.connect(persist_bool_option("randomize_elevators"))

        # Trick Selection
        self.trick_checkboxes: Dict[SimpleResourceInfo, QtWidgets.QCheckBox] = {}
        self.create_trick_checkboxes()
        self.selectNoTricks.clicked.connect(self.unselect_all_tricks)
        self.selectAllTricks.clicked.connect(self.select_all_tricks)

    def on_min_difficulty_changed(self, new_value: int):
        options = application_options()
        try:
            options.minimum_difficulty = new_value
            options.save_to_disk()
        except ValueError:
            self.minimumDifficulty.setValue(options.minimum_difficulty)

    def on_max_difficulty_changed(self, new_value: int):
        options = application_options()
        try:
            options.maximum_difficulty = new_value
            options.save_to_disk()
        except ValueError:
            self.maximumDifficulty.setValue(options.maximum_difficulty)

    def create_trick_checkboxes(self):
        enabled_tricks = application_options().enabled_tricks

        for trick in sorted(self.resource_database.trick, key=lambda x: x.long_name):
            checkbox = QtWidgets.QCheckBox(self.tricksContents)
            checkbox.setChecked(trick.index in enabled_tricks)
            checkbox.setCheckable(True)
            self.tricksContentLayout.addWidget(checkbox)

            checkbox.setText(QtCore.QCoreApplication.translate(
                "EchoesDatabase", trick.long_name, "trick"))
            checkbox.stateChanged.connect(self.on_trick_checked_changed)
            self.trick_checkboxes[trick] = checkbox

    def on_trick_checked_changed(self):
        if self._on_bulk_change:
            return

        options = application_options()
        options.enabled_tricks = {
            trick
            for trick, checkbox in self.trick_checkboxes.items()
            if checkbox.isChecked()
        }
        options.save_to_disk()

    def select_all_tricks(self):
        self._on_bulk_change = True
        _map_set_checked(self.trick_checkboxes.values(), True)
        self._on_bulk_change = False
        self.on_trick_checked_changed()

    def unselect_all_tricks(self):
        self._on_bulk_change = True
        _map_set_checked(self.trick_checkboxes.values(), False)
        self._on_bulk_change = False
        self.on_trick_checked_changed()
