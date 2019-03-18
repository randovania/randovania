import collections
import dataclasses
import functools
from functools import partial
from typing import Dict, Tuple, List, Iterable

from PySide2.QtCore import QRect, Qt
from PySide2.QtWidgets import QMainWindow, QLabel, QGroupBox, QGridLayout, QToolButton, QSizePolicy, QDialog, QSpinBox, \
    QHBoxLayout, QWidget

from randovania.game_description.default_database import default_prime2_item_database, default_prime2_resource_database
from randovania.game_description.item.ammo import Ammo
from randovania.game_description.item.item_database import ItemDatabase
from randovania.game_description.item.major_item import MajorItem
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.resource_type import ResourceType
from randovania.gui.background_task_mixin import BackgroundTaskMixin
from randovania.gui.item_configuration_popup import ItemConfigurationPopup
from randovania.gui.main_rules_ui import Ui_MainRules
from randovania.gui.tab_service import TabService
from randovania.interface_common.options import Options
from randovania.layout.ammo_state import AmmoState
from randovania.layout.major_item_state import ENERGY_TANK_MAXIMUM_COUNT, MajorItemState
from randovania.resolver.exceptions import InvalidConfiguration
from randovania.resolver.item_pool.ammo import items_for_ammo

_EXPECTED_COUNT_TEXT_TEMPLATE = ("Each expansion will provide, on average, {per_expansion} for a total of {total}."
                                 "\n{from_items} will be provided from major items.")

AmmoPickupWidgets = Tuple[QSpinBox, QLabel, QToolButton, QLabel, QGroupBox]


def _toggle_box_visibility(toggle_button: QToolButton, box: QGroupBox):
    box.setVisible(not box.isVisible())
    toggle_button.setText("-" if box.isVisible() else "+")


def _update_ammo_visibility(elements: AmmoPickupWidgets, is_visible: bool):
    elements[2].setVisible(is_visible)
    elements[3].setVisible(is_visible)
    if elements[2].text() == "-":
        elements[4].setVisible(is_visible)


def _update_elements_for_progressive_item(elements: Dict[MajorItem, Iterable[QWidget]],
                                          non_progressive_items: Iterable[MajorItem],
                                          progressive_item: MajorItem,
                                          is_progressive: bool,
                                          ):
    for item in non_progressive_items:
        for element in elements[item]:
            element.setVisible(not is_progressive)

    for element in elements[progressive_item]:
        element.setVisible(is_progressive)


class MainRulesWindow(QMainWindow, Ui_MainRules):
    _boxes_for_category: Dict[
        ItemCategory, Tuple[QGroupBox, QGridLayout, Dict[MajorItem, Tuple[QToolButton, QLabel]]]]

    _ammo_maximum_spinboxes: Dict[int, List[QSpinBox]]
    _ammo_pickup_widgets: Dict[Ammo, AmmoPickupWidgets]

    def __init__(self, tab_service: TabService, background_processor: BackgroundTaskMixin, options: Options):
        super().__init__()
        self.setupUi(self)

        self._options = options
        size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.gridLayout.setAlignment(Qt.AlignTop)

        # Relevant Items
        item_database = default_prime2_item_database()

        self._dark_suit = item_database.major_items["Dark Suit"]
        self._light_suit = item_database.major_items["Light Suit"]
        self._progressive_suit = item_database.major_items["Progressive Suit"]
        self._grapple_beam = item_database.major_items["Grapple Beam"]
        self._screw_attack = item_database.major_items["Screw Attack"]
        self._progressive_grapple = item_database.major_items["Progressive Grapple"]
        self._energy_tank_item = item_database.major_items["Energy Tank"]
        self._dark_ammo_item = item_database.ammo["Dark Ammo Expansion"]
        self._light_ammo_item = item_database.ammo["Light Ammo Expansion"]
        self._beam_ammo_item = item_database.ammo["Beam Ammo Expansion"]

        self._register_alternatives_events()
        self._create_categories_boxes(size_policy)
        self._create_major_item_boxes(item_database)
        self._create_energy_tank_box()
        self._create_ammo_pickup_boxes(size_policy, item_database)

    def on_options_changed(self, options: Options):
        # Item alternatives
        layout = options.layout_configuration
        major_configuration = options.major_items_configuration

        self.progressive_suit_check.setChecked(major_configuration.progressive_suit)
        self.progressive_grapple_check.setChecked(major_configuration.progressive_grapple)
        self.split_ammo_check.setChecked(layout.split_beam_ammo)

        _update_elements_for_progressive_item(
            self._boxes_for_category[ItemCategory.SUIT][2],
            [self._dark_suit, self._light_suit],
            self._progressive_suit,
            major_configuration.progressive_suit
        )

        _update_elements_for_progressive_item(
            self._boxes_for_category[ItemCategory.MOVEMENT][2],
            [self._grapple_beam, self._screw_attack],
            self._progressive_grapple,
            major_configuration.progressive_grapple
        )

        _update_ammo_visibility(self._ammo_pickup_widgets[self._beam_ammo_item], not layout.split_beam_ammo)
        for item in [self._dark_ammo_item, self._light_ammo_item]:
            _update_ammo_visibility(self._ammo_pickup_widgets[item], layout.split_beam_ammo)

        # Energy Tank
        energy_tank_state = major_configuration.items_state[self._energy_tank_item]

        self.energy_tank_starting_spinbox.setValue(energy_tank_state.num_included_in_starting_items)
        self.energy_tank_shuffled_spinbox.setValue(energy_tank_state.num_shuffled_pickups)

        # Ammo
        ammo_provided = major_configuration.calculate_provided_ammo()
        ammo_configuration = options.ammo_configuration

        for ammo_item, maximum in ammo_configuration.maximum_ammo.items():
            for spinbox in self._ammo_maximum_spinboxes[ammo_item]:
                spinbox.setValue(maximum)

        previous_pickup_for_item = {}
        resource_database = default_prime2_resource_database()

        item_for_index = {
            ammo_index: resource_database.get_by_type_and_index(ResourceType.ITEM, ammo_index)
            for ammo_index in ammo_provided.keys()
        }

        for ammo, state in ammo_configuration.items_state.items():
            self._ammo_pickup_widgets[ammo][0].setValue(state.pickup_count)

            try:
                ammo_per_pickup = items_for_ammo(ammo, state, ammo_provided,
                                                 previous_pickup_for_item,
                                                 ammo_configuration.maximum_ammo)

                totals = functools.reduce(lambda a, b: [x + y for x, y in zip(a, b)],
                                          ammo_per_pickup,
                                          [0 for _ in ammo.items])

                if state.pickup_count == 0:
                    self._ammo_pickup_widgets[ammo][1].setText("No expansions will be created.")
                    continue

                self._ammo_pickup_widgets[ammo][1].setText(
                    _EXPECTED_COUNT_TEXT_TEMPLATE.format(
                        per_expansion=" and ".join(
                            "{} {}".format(
                                total // state.pickup_count,
                                item_for_index[ammo_index].long_name
                            )
                            for ammo_index, total in zip(ammo.items, totals)
                        ),
                        total=" and ".join(
                            "{} {}".format(
                                total,
                                item_for_index[ammo_index].long_name
                            )
                            for ammo_index, total in zip(ammo.items, totals)
                        ),
                        from_items=" and ".join(
                            "{} {}".format(
                                ammo_provided[ammo_index],
                                item_for_index[ammo_index].long_name
                            )
                            for ammo_index in ammo.items
                        ),
                    )
                )

            except InvalidConfiguration as invalid_config:
                self._ammo_pickup_widgets[ammo][1].setText(str(invalid_config))

    # Item Alternatives

    def _register_alternatives_events(self):
        self.progressive_suit_check.stateChanged.connect(
            self._persist_bool_major_configuration_field("progressive_suit"))
        self.progressive_suit_check.clicked.connect(self._change_progressive_suit)

        self.progressive_grapple_check.stateChanged.connect(
            self._persist_bool_major_configuration_field("progressive_grapple"))
        self.progressive_grapple_check.clicked.connect(self._change_progressive_grapple)

        self.split_ammo_check.stateChanged.connect(self._persist_bool_layout_field("split_beam_ammo"))
        self.split_ammo_check.clicked.connect(self._change_split_ammo)

    def _persist_bool_layout_field(self, field_name: str):
        def bound(value: int):
            with self._options as options:
                options.set_layout_configuration_field(field_name, bool(value))

        return bound

    def _persist_bool_major_configuration_field(self, field_name: str):
        def bound(value: int):
            with self._options as options:
                kwargs = {field_name: bool(value)}
                options.major_items_configuration = dataclasses.replace(options.major_items_configuration, **kwargs)

        return bound

    def _change_progressive_suit(self, has_progressive: bool):
        with self._options as options:
            major_configuration = options.major_items_configuration

            if has_progressive:
                dark_suit_state = MajorItemState()
                light_suit_state = MajorItemState()
                progressive_suit_state = MajorItemState(num_shuffled_pickups=2)
            else:
                dark_suit_state = MajorItemState(num_shuffled_pickups=1)
                light_suit_state = MajorItemState(num_shuffled_pickups=1)
                progressive_suit_state = MajorItemState()

            major_configuration = major_configuration.replace_states({
                self._dark_suit: dark_suit_state,
                self._light_suit: light_suit_state,
                self._progressive_suit: progressive_suit_state,
            })

            options.major_items_configuration = major_configuration

    def _change_progressive_grapple(self, has_progressive: bool):
        with self._options as options:
            major_configuration = options.major_items_configuration

            if has_progressive:
                grapple_state = MajorItemState()
                screw_state = MajorItemState()
                progressive_state = MajorItemState(num_shuffled_pickups=2)
            else:
                grapple_state = MajorItemState(num_shuffled_pickups=1)
                screw_state = MajorItemState(num_shuffled_pickups=1)
                progressive_state = MajorItemState()

            major_configuration = major_configuration.replace_states({
                self._grapple_beam: grapple_state,
                self._screw_attack: screw_state,
                self._progressive_grapple: progressive_state,
            })

            options.major_items_configuration = major_configuration

    def _change_split_ammo(self, has_split: bool):
        with self._options as options:
            ammo_configuration = options.ammo_configuration

            current_total = sum(
                ammo_configuration.items_state[ammo].pickup_count
                for ammo in (self._dark_ammo_item, self._light_ammo_item, self._beam_ammo_item)
            )
            if has_split:
                dark_ammo_state = AmmoState(pickup_count=current_total // 2)
                light_ammo_state = AmmoState(pickup_count=current_total // 2)
                beam_ammo_state = AmmoState()
            else:
                dark_ammo_state = AmmoState()
                light_ammo_state = AmmoState()
                beam_ammo_state = AmmoState(pickup_count=current_total)

            ammo_configuration = ammo_configuration.replace_states({
                self._dark_ammo_item: dark_ammo_state,
                self._light_ammo_item: light_ammo_state,
                self._beam_ammo_item: beam_ammo_state,
            })

            options.ammo_configuration = ammo_configuration

    # Major Items

    def _create_categories_boxes(self, size_policy):
        self._boxes_for_category = {}

        current_row = 0
        for major_item_category in ItemCategory:
            if not major_item_category.is_major_category:
                continue

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

            self.major_items_layout.addWidget(category_button, 2 * current_row + 1, 0, 1, 1)
            self.major_items_layout.addWidget(category_label, 2 * current_row + 1, 1, 1, 1)
            self.major_items_layout.addWidget(category_box, 2 * current_row + 2, 0, 1, 2)
            self._boxes_for_category[major_item_category] = category_box, category_layout, {}

            category_button.clicked.connect(partial(_toggle_box_visibility, category_button, category_box))
            category_box.setVisible(False)
            current_row += 1

    def _create_major_item_boxes(self, item_database: ItemDatabase):
        for major_item in item_database.major_items.values():
            if major_item.required or major_item.item_category == ItemCategory.ENERGY_TANK:
                continue
            category_box, category_layout, elements = self._boxes_for_category[major_item.item_category]

            item_button = QToolButton(category_box)
            item_button.setGeometry(QRect(20, 30, 24, 21))
            item_button.setText("...")

            item_label = QLabel(category_box)
            item_label.setText(major_item.name)

            i = len(elements)
            category_layout.addWidget(item_button, i, 0)
            category_layout.addWidget(item_label, i, 1)
            elements[major_item] = item_button, item_label

            item_button.clicked.connect(partial(self.show_item_popup, major_item))

    def show_item_popup(self, item: MajorItem):
        """
        Shows the ItemConfigurationPopup for the given MajorItem
        :param item:
        :return:
        """
        major_items_configuration = self._options.major_items_configuration

        popup = ItemConfigurationPopup(self, item, major_items_configuration.items_state[item])
        result = popup.exec_()

        if result == QDialog.Accepted:
            with self._options:
                self._options.major_items_configuration = major_items_configuration.replace_state_for_item(
                    item, popup.state
                )

    # Energy Tank

    def _create_energy_tank_box(self):
        category_box, category_layout, _ = self._boxes_for_category[ItemCategory.ENERGY_TANK]

        starting_label = QLabel(category_box)
        starting_label.setText("Starting Quantity")

        shuffled_label = QLabel(category_box)
        shuffled_label.setText("Shuffled Quantity")

        self.energy_tank_starting_spinbox = QSpinBox(category_box)
        self.energy_tank_starting_spinbox.setMaximum(ENERGY_TANK_MAXIMUM_COUNT)
        self.energy_tank_starting_spinbox.valueChanged.connect(self._on_update_starting_energy_tank)
        self.energy_tank_shuffled_spinbox = QSpinBox(category_box)
        self.energy_tank_shuffled_spinbox.setMaximum(ENERGY_TANK_MAXIMUM_COUNT)
        self.energy_tank_shuffled_spinbox.valueChanged.connect(self._on_update_shuffled_energy_tank)

        category_layout.addWidget(starting_label, 0, 0)
        category_layout.addWidget(self.energy_tank_starting_spinbox, 0, 1)
        category_layout.addWidget(shuffled_label, 1, 0)
        category_layout.addWidget(self.energy_tank_shuffled_spinbox, 1, 1)

    def _on_update_starting_energy_tank(self, value: int):
        with self._options as options:
            major_configuration = options.major_items_configuration
            options.major_items_configuration = major_configuration.replace_state_for_item(
                self._energy_tank_item,
                dataclasses.replace(major_configuration.items_state[self._energy_tank_item],
                                    num_included_in_starting_items=value)
            )

    def _on_update_shuffled_energy_tank(self, value: int):
        with self._options as options:
            major_configuration = options.major_items_configuration
            options.major_items_configuration = major_configuration.replace_state_for_item(
                self._energy_tank_item,
                dataclasses.replace(major_configuration.items_state[self._energy_tank_item],
                                    num_shuffled_pickups=value)
            )

    # Ammo

    def _create_ammo_pickup_boxes(self, size_policy, item_database: ItemDatabase):
        """
        Creates the GroupBox with SpinBoxes for selecting the pickup count of all the ammo
        :param item_database:
        :return:
        """

        self._ammo_maximum_spinboxes = collections.defaultdict(list)
        self._ammo_pickup_widgets = {}

        resource_database = default_prime2_resource_database()

        for ammo in item_database.ammo.values():
            title_layout = QHBoxLayout()
            title_layout.setObjectName(f"{ammo.name} Title Horizontal Layout")

            expand_ammo_button = QToolButton(self.ammo_box)
            expand_ammo_button.setGeometry(QRect(20, 30, 24, 21))
            expand_ammo_button.setText("+")
            title_layout.addWidget(expand_ammo_button)

            category_label = QLabel(self.ammo_box)
            category_label.setSizePolicy(size_policy)
            category_label.setText(ammo.name)
            title_layout.addWidget(category_label)

            pickup_box = QGroupBox(self.ammo_box)
            pickup_box.setSizePolicy(size_policy)
            layout = QGridLayout(pickup_box)
            layout.setObjectName(f"{ammo.name} Box Layout")
            current_row = 0

            for ammo_item in ammo.items:
                item = resource_database.get_by_type_and_index(ResourceType.ITEM, ammo_item)

                target_count_label = QLabel(pickup_box)
                target_count_label.setText(f"{item.long_name} Target" if len(ammo.items) > 1 else "Target count")

                maximum_spinbox = QSpinBox(pickup_box)
                maximum_spinbox.setMaximum(ammo.maximum)
                maximum_spinbox.valueChanged.connect(partial(self._on_update_ammo_maximum_spinbox, ammo_item))
                self._ammo_maximum_spinboxes[ammo_item].append(maximum_spinbox)

                layout.addWidget(target_count_label, current_row, 0)
                layout.addWidget(maximum_spinbox, current_row, 1)
                current_row += 1

            count_label = QLabel(pickup_box)
            count_label.setText("Pickup Count")
            count_label.setToolTip("How many instances of this expansion should be placed.")

            pickup_spinbox = QSpinBox(pickup_box)
            pickup_spinbox.setMaximum(AmmoState.maximum_pickup_count())
            pickup_spinbox.valueChanged.connect(partial(self._on_update_ammo_pickup_spinbox, ammo))

            layout.addWidget(count_label, current_row, 0)
            layout.addWidget(pickup_spinbox, current_row, 1)
            current_row += 1

            expected_count = QLabel(pickup_box)
            expected_count.setWordWrap(True)
            expected_count.setText(_EXPECTED_COUNT_TEXT_TEMPLATE)
            expected_count.setToolTip("Some expansions may provide 1 extra, even with no variance, if the total count "
                                      "is not divisible by the pickup count.")
            layout.addWidget(expected_count, current_row, 0, 1, 2)
            current_row += 1

            self._ammo_pickup_widgets[ammo] = (pickup_spinbox, expected_count, expand_ammo_button,
                                               category_label, pickup_box)

            expand_ammo_button.clicked.connect(partial(_toggle_box_visibility, expand_ammo_button, pickup_box))
            pickup_box.setVisible(False)

            self.ammo_layout.addLayout(title_layout)
            self.ammo_layout.addWidget(pickup_box)

    def _on_update_ammo_maximum_spinbox(self, ammo_int: int, value: int):
        with self._options as options:
            options.ammo_configuration = options.ammo_configuration.replace_maximum_for_item(
                ammo_int, value
            )

    def _on_update_ammo_pickup_spinbox(self, ammo: Ammo, value: int):
        with self._options as options:
            ammo_configuration = options.ammo_configuration
            options.ammo_configuration = ammo_configuration.replace_state_for_ammo(
                ammo,
                dataclasses.replace(ammo_configuration.items_state[ammo], pickup_count=value)
            )
