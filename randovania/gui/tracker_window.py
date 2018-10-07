from PyQt5.QtWidgets import QMainWindow, QTreeWidgetItem, QListWidgetItem

from randovania.game_description import data_reader
from randovania.games.prime import binary_data
from randovania.gui.tracker_window_ui import Ui_TrackerWindow


class TrackerWindow(QMainWindow, Ui_TrackerWindow):

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        data = binary_data.decode_default_prime2()
        resource_database = data_reader.read_resource_database(data["resource_database"])

        self.items_tree_widget.setSortingEnabled(False)
        for item in resource_database.item:
            tree_item = QTreeWidgetItem(self.items_tree_widget)
            tree_item.setText(0, item.long_name)
            tree_item.setText(1, "1")
        self.items_tree_widget.setSortingEnabled(True)

        for event in resource_database.event:
            list_item = QListWidgetItem()
            list_item.setText(event.long_name)
            self.events_list_widget.addItem(list_item)
        self.events_list_widget.sortItems()
