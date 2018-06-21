from typing import Dict, Iterator

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMainWindow

from randovania.games.prime import binary_data
from randovania.gui import application_options
from randovania.gui.randomizer_configuration_window_ui import Ui_RandomizeWindow
from randovania.resolver.data_reader import read_resource_database
from randovania.resolver.resources import SimpleResourceInfo


def _map_set_checked(iterable: Iterator[QtWidgets.QCheckBox], new_status: bool):
    for checkbox in iterable:
        checkbox.setChecked(new_status)


def _persist_bool_option(attribute_name: str):
    def callback(value: bool):
        options = application_options()
        setattr(options, attribute_name, value)
        options.save_to_disk()

    return callback


class RandomizeWindow(QMainWindow, Ui_RandomizeWindow):
    def __init__(self):
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
        self.removeItemLoss.setChecked(options.remove_item_loss)
        self.removeItemLoss.stateChanged.connect(_persist_bool_option("remove_item_loss"))
        self.randomizeElevators.setChecked(options.randomize_elevators)
        self.randomizeElevators.stateChanged.connect(_persist_bool_option("randomize_elevators"))
        self.removeHudPopup.setChecked(options.hud_memo_popup_removal)
        self.removeHudPopup.stateChanged.connect(_persist_bool_option("hud_memo_popup_removal"))

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
