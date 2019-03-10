from functools import partial

from PySide2.QtCore import QRect, Qt
from PySide2.QtWidgets import QMainWindow, QLabel, QGroupBox, QGridLayout, QToolButton, QSizePolicy, QDialog

from randovania.game_description.default_database import default_prime2_item_database
from randovania.game_description.item.major_item import MajorItemCategory, MajorItem
from randovania.gui.background_task_mixin import BackgroundTaskMixin
from randovania.gui.item_configuration_popup import ItemConfigurationPopup
from randovania.gui.main_rules_ui import Ui_MainRules
from randovania.gui.tab_service import TabService
from randovania.interface_common.options import Options


def _toggle_category_visibility(category_button: QToolButton, category_box: QGroupBox):
    category_box.setVisible(not category_box.isVisible())
    category_button.setText("-" if category_box.isVisible() else "+")


class MainRulesWindow(QMainWindow, Ui_MainRules):

    def __init__(self, tab_service: TabService, background_processor: BackgroundTaskMixin, options: Options):
        super().__init__()
        self.setupUi(self)

        self._options = options
        size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.gridLayout.setAlignment(Qt.AlignTop)

        # Create Stuff
        self._create_categories_boxes(size_policy)
        self._create_major_item_boxes()

    def on_options_changed(self):
        pass

    def _create_categories_boxes(self, size_policy):
        self._boxes_for_category = {}

        for i, major_item_category in enumerate(MajorItemCategory):
            category_button = QToolButton(self.major_items_box)
            category_button.setGeometry(QRect(20, 30, 24, 21))
            category_button.setText("+")

            category_label = QLabel(self.major_items_box)
            category_label.setSizePolicy(size_policy)
            category_label.setText(major_item_category.value)

            category_box = QGroupBox(self.major_items_box)
            category_box.setSizePolicy(size_policy)
            category_box.setObjectName(f"category_box {major_item_category}")

            category_layout = QGridLayout(category_box)
            category_layout.setObjectName(f"category_layout {major_item_category}")

            self.major_items_layout.addWidget(category_button, 2 * i + 1, 0, 1, 1)
            self.major_items_layout.addWidget(category_label, 2 * i + 1, 1, 1, 1)
            self.major_items_layout.addWidget(category_box, 2 * i + 2, 0, 1, 2)
            self._boxes_for_category[major_item_category] = category_box, category_layout, []

            category_button.clicked.connect(partial(_toggle_category_visibility, category_button, category_box))
            category_box.setVisible(False)

    def _create_major_item_boxes(self):
        item_database = default_prime2_item_database()

        for major_item in item_database.major_items.values():
            category_box, category_layout, elements = self._boxes_for_category[major_item.item_category]

            item_button = QToolButton(category_box)
            item_button.setGeometry(QRect(20, 30, 24, 21))
            item_button.setText("...")

            item_label = QLabel(category_box)
            item_label.setText(major_item.name)

            i = len(elements)
            category_layout.addWidget(item_button, i, 0)
            category_layout.addWidget(item_label, i, 1)
            elements.append((major_item, item_button, item_label))

            item_button.clicked.connect(partial(self.show_item_popup, major_item))

    def show_item_popup(self, item: MajorItem):
        major_items_configuration = self._options.major_items_configuration

        popup = ItemConfigurationPopup(self, item, major_items_configuration.items_state[item])
        result = popup.exec_()

        if result == QDialog.Accepted:
            with self._options:
                self._options.major_items_configuration = major_items_configuration.replace_state_for_item(
                    item, popup.state
                )
