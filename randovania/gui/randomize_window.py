import os
from typing import Dict, Iterable, List

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMainWindow

from randovania import get_data_path
from randovania.games.prime import binary_data
from randovania.games.prime.log_parser import parse_log
from randovania.gui.randomize_window_ui import Ui_RandomizeWindow
from randovania.resolver.data_reader import read_resource_database
from randovania.resolver.game_description import SimpleResourceInfo


def _map_set_checked(iterable: Iterable[QtWidgets.QCheckBox], new_status: bool):
    for checkbox in iterable:
        checkbox.setChecked(True)


class RandomizeWindow(QMainWindow, Ui_RandomizeWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        data_file_path = os.path.join(get_data_path(), "prime2.bin")
        with open(data_file_path, "rb") as x:  # type: BinaryIO
            data = binary_data.decode(x)
        self.resource_database = read_resource_database(data["resource_database"])
        self.original_log = parse_log(os.path.join(get_data_path(), "prime2_original_log.txt"))

        # Trick Selection
        self.trick_checkboxes: Dict[SimpleResourceInfo, QtWidgets.QCheckBox] = {}
        self.create_trick_checkboxes()
        self.selectNoTricks.clicked.connect(self.unselect_all_tricks)
        self.selectAllTricks.clicked.connect(self.select_all_tricks)

        # Exclusion Selection
        self.exclude_checkboxes: List[QtWidgets.QCheckBox] = [None] * len(self.original_log.pickup_database.entries)
        self.create_exclusion_checkboxes()
        self.clearExcludedPickups.clicked.connect(self.unselect_all_exclusions)


    def create_trick_checkboxes(self):
        for trick in sorted(self.resource_database.trick, key=lambda x: x.long_name):
            trick_checkbox = QtWidgets.QCheckBox(self.tricksContents)
            trick_checkbox.setCheckable(True)
            self.tricksContentLayout.addWidget(trick_checkbox)

            trick_checkbox.setText(QtCore.QCoreApplication.translate(
                "EchoesDatabase", trick.long_name, "trick"))
            self.trick_checkboxes[trick] = trick_checkbox

    def select_all_tricks(self):
        _map_set_checked(self.trick_checkboxes.values(), True)

    def unselect_all_tricks(self):
        _map_set_checked(self.trick_checkboxes.values(), False)

    def create_exclusion_checkboxes(self):
        for i, entry in enumerate(self.original_log.pickup_database.entries):
            checkbox = QtWidgets.QCheckBox(self.excludedItemsContents)
            checkbox.setCheckable(True)
            self.excludedItemsContentLayout.addWidget(checkbox)

            lol = "{} - {} - {}".format(
                QtCore.QCoreApplication.translate("EchoesDatabase", entry.world, "world"),
                QtCore.QCoreApplication.translate("EchoesDatabase", entry.room, "room"),
                QtCore.QCoreApplication.translate("EchoesDatabase", entry.item, "item")
            )
            checkbox.setText(lol)
            self.exclude_checkboxes[i] = checkbox

    def unselect_all_exclusions(self):
        pass
        # _map_set_checked(self.exclude_checkboxes, False)
