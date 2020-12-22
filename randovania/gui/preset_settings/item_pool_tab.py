import collections
import dataclasses
import functools
from functools import partial
from typing import Dict, Tuple, List, Optional

from PySide2.QtCore import QRect, Qt
from PySide2.QtWidgets import QLabel, QGroupBox, QGridLayout, QToolButton, QSizePolicy, QDialog, QSpinBox, \
    QHBoxLayout, QCheckBox

from randovania.game_description import default_database
from randovania.game_description.item.ammo import Ammo
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.item.item_database import ItemDatabase
from randovania.game_description.item.major_item import MajorItem
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.resource_type import ResourceType
from randovania.games.game import RandovaniaGame
from randovania.generator.item_pool import pool_creator
from randovania.generator.item_pool.ammo import items_for_ammo
from randovania.gui.dialog.item_configuration_popup import ItemConfigurationPopup
from randovania.gui.generated.preset_item_pool_ui import Ui_PresetItemPool
from randovania.gui.lib import common_qt_lib
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.gui.preset_settings.progressive_item_widget import ProgressiveItemWidget
from randovania.gui.preset_settings.split_ammo_widget import SplitAmmoWidget
from randovania.interface_common.enum_lib import iterate_enum
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.ammo_state import AmmoState
from randovania.layout.major_item_state import ENERGY_TANK_MAXIMUM_COUNT, DEFAULT_MAXIMUM_SHUFFLED
from randovania.layout.preset import Preset
from randovania.resolver.exceptions import InvalidConfiguration

_EXPECTED_COUNT_TEXT_TEMPLATE = ("Each expansion will provide, on average, {per_expansion}, for a total of {total}."
                                 "\n{from_items} will be provided from major items.")
_EXPECTED_COUNT_TEXT_TEMPLATE_EXACT = ("Each expansion will provide exactly {per_expansion}, for a total of {total}."
                                       "\n{from_items} will be provided from major items.")

AmmoPickupWidgets = Tuple[QSpinBox, QLabel, QToolButton, QLabel, QGroupBox, Optional[QCheckBox]]


def _toggle_box_visibility(toggle_button: QToolButton, box: QGroupBox):
    box.setVisible(not box.isVisible())
    toggle_button.setText("-" if box.isVisible() else "+")


class PresetItemPool(PresetTab, Ui_PresetItemPool):
    _boxes_for_category: Dict[
        ItemCategory, Tuple[QGroupBox, QGridLayout, Dict[MajorItem, Tuple[QToolButton, QLabel]]]]

    _ammo_maximum_spinboxes: Dict[int, List[QSpinBox]]
    _ammo_pickup_widgets: Dict[Ammo, AmmoPickupWidgets]
    _progressive_widgets: List[ProgressiveItemWidget]
    _split_ammo_widgets: List[SplitAmmoWidget]

    def __init__(self, editor: PresetEditor):
        super().__init__()
        self.setupUi(self)

        self._editor = editor
        size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.gridLayout.setAlignment(Qt.AlignTop)

        # Relevant Items
        self.game = editor.game
        item_database = default_database.item_database_for_game(self.game)

        self._energy_tank_item = item_database.major_items["Energy Tank"]

        self._register_random_starting_events()
        self._create_progressive_widgets(item_database)
        self._create_split_ammo_widgets(item_database)
        self._create_categories_boxes(item_database, size_policy)
        self._create_major_item_boxes(item_database)
        self._create_energy_tank_box()
        self._create_ammo_pickup_boxes(size_policy, item_database)

    @property
    def uses_patches_tab(self) -> bool:
        return False

    def on_preset_changed(self, preset: Preset):
        # Item alternatives
        layout = preset.configuration
        major_configuration = layout.major_items_configuration

        for progressive_widget in self._progressive_widgets:
            progressive_widget.on_preset_changed(
                preset,
                self._boxes_for_category[progressive_widget.progressive_item.item_category][2],
            )

        for split_ammo in self._split_ammo_widgets:
            split_ammo.on_preset_changed(preset, self._ammo_pickup_widgets)

        # Random Starting Items
        self.minimum_starting_spinbox.setValue(major_configuration.minimum_random_starting_items)
        self.maximum_starting_spinbox.setValue(major_configuration.maximum_random_starting_items)

        # Energy Tank
        energy_tank_state = major_configuration.items_state[self._energy_tank_item]

        self.energy_tank_starting_spinbox.setValue(energy_tank_state.num_included_in_starting_items)
        self.energy_tank_shuffled_spinbox.setValue(energy_tank_state.num_shuffled_pickups)

        # Ammo
        ammo_provided = major_configuration.calculate_provided_ammo()
        ammo_configuration = layout.ammo_configuration

        for ammo_item, maximum in ammo_configuration.maximum_ammo.items():
            for spinbox in self._ammo_maximum_spinboxes[ammo_item]:
                spinbox.setValue(maximum)

        previous_pickup_for_item = {}
        game = default_database.game_description_for(self.game)
        resource_database = game.resource_database

        item_for_index: Dict[int, ItemResourceInfo] = {
            ammo_index: resource_database.get_item(ammo_index)
            for ammo_index in ammo_provided.keys()
        }

        for ammo, state in ammo_configuration.items_state.items():
            self._ammo_pickup_widgets[ammo][0].setValue(state.pickup_count)

            if self._ammo_pickup_widgets[ammo][5] is not None:
                self._ammo_pickup_widgets[ammo][5].setChecked(state.requires_major_item)

            try:
                if state.pickup_count == 0:
                    self._ammo_pickup_widgets[ammo][1].setText("No expansions will be created.")
                    continue

                ammo_per_pickup = items_for_ammo(ammo, state, ammo_provided,
                                                 previous_pickup_for_item,
                                                 ammo_configuration.maximum_ammo)

                totals = functools.reduce(lambda a, b: [x + y for x, y in zip(a, b)],
                                          ammo_per_pickup,
                                          [0 for _ in ammo.items])

                if {total % state.pickup_count for total in totals} == {0}:
                    count_text_template = _EXPECTED_COUNT_TEXT_TEMPLATE_EXACT
                else:
                    count_text_template = _EXPECTED_COUNT_TEXT_TEMPLATE

                self._ammo_pickup_widgets[ammo][1].setText(
                    count_text_template.format(
                        per_expansion=" and ".join(
                            "{:.3g} {}".format(
                                total / state.pickup_count,
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

        # Item pool count
        try:
            pool_pickup = pool_creator.calculate_pool_results(layout, resource_database).pickups
            min_starting_items = layout.major_items_configuration.minimum_random_starting_items
            maximum_size = game.world_list.num_pickup_nodes + min_starting_items
            self.item_pool_count_label.setText(
                "Items in pool: {}/{}".format(len(pool_pickup), maximum_size)
            )
            common_qt_lib.set_error_border_stylesheet(self.item_pool_count_label, len(pool_pickup) > maximum_size)

        except InvalidConfiguration as invalid_config:
            self.item_pool_count_label.setText("Invalid Configuration: {}".format(invalid_config))
            common_qt_lib.set_error_border_stylesheet(self.item_pool_count_label, True)

    # Item Alternatives

    def _persist_bool_layout_field(self, field_name: str):
        def bound(value: int):
            with self._editor as options:
                options.set_configuration_field(field_name, bool(value))

        return bound

    def _persist_bool_major_configuration_field(self, field_name: str):
        def bound(value: int):
            with self._editor as options:
                kwargs = {field_name: bool(value)}
                options.major_items_configuration = dataclasses.replace(options.major_items_configuration, **kwargs)

        return bound

    # Random Starting

    def _register_random_starting_events(self):
        self.minimum_starting_spinbox.valueChanged.connect(self._on_update_minimum_starting)
        self.maximum_starting_spinbox.valueChanged.connect(self._on_update_maximum_starting)

    def _on_update_minimum_starting(self, value: int):
        with self._editor as options:
            options.major_items_configuration = dataclasses.replace(options.major_items_configuration,
                                                                    minimum_random_starting_items=value)

    def _on_update_maximum_starting(self, value: int):
        with self._editor as options:
            options.major_items_configuration = dataclasses.replace(options.major_items_configuration,
                                                                    maximum_random_starting_items=value)

    # Major Items
    def _create_progressive_widgets(self, item_database: ItemDatabase):
        self._progressive_widgets = []

        all_progressive = []

        if self.game == RandovaniaGame.PRIME2:
            all_progressive.append((
                "Progressive Suit",
                ("Dark Suit", "Light Suit"),
            ))
            all_progressive.append((
                "Progressive Grapple",
                ("Grapple Beam", "Screw Attack"),
            ))
        elif self.game == RandovaniaGame.PRIME3:
            all_progressive.append((
                "Progressive Missile",
                ("Ice Missile", "Seeker Missile"),
            ))
            all_progressive.append((
                "Progressive Beam",
                ("Plasma Beam", "Nova Beam"),
            ))

        for (progressive_item, non_progressive_items) in all_progressive:
            widget = ProgressiveItemWidget(
                self.item_alternative_box, self._editor,
                progressive_item=item_database.major_items[progressive_item],
                non_progressive_items=[item_database.major_items[it]
                                       for it in non_progressive_items],
            )
            widget.setText("Use progressive {}".format(" → ".join(non_progressive_items)))
            self._progressive_widgets.append(widget)
            self.item_alternative_layout.addWidget(widget)

    def _create_split_ammo_widgets(self, item_database: ItemDatabase):
        self._split_ammo_widgets = []

        if self.game == RandovaniaGame.PRIME2:
            beam_ammo = SplitAmmoWidget(
                self.item_alternative_box, self._editor,
                unified_ammo=item_database.ammo["Beam Ammo Expansion"],
                split_ammo=[
                    item_database.ammo["Dark Ammo Expansion"],
                    item_database.ammo["Light Ammo Expansion"],
                ],
            )
            beam_ammo.setText("Split Beam Ammo Expansions")
            self._split_ammo_widgets.append(beam_ammo)

        for widget in self._split_ammo_widgets:
            self.item_alternative_layout.addWidget(widget)

    def _create_categories_boxes(self, item_database: ItemDatabase, size_policy):
        self._boxes_for_category = {}

        categories = set()
        for major_item in item_database.major_items.values():
            if not major_item.required:
                categories.add(major_item.item_category)

        all_categories = list(iterate_enum(ItemCategory))

        current_row = 0
        for major_item_category in sorted(categories, key=lambda it: all_categories.index(it)):
            category_button = QToolButton(self.major_items_box)
            category_button.setGeometry(QRect(20, 30, 24, 21))
            category_button.setText("+")

            category_label = QLabel(self.major_items_box)
            category_label.setSizePolicy(size_policy)
            category_label.setText(major_item_category.long_name)

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
        major_items_configuration = self._editor.major_items_configuration

        popup = ItemConfigurationPopup(self, item, major_items_configuration.items_state[item],
                                       default_database.resource_database_for(self.game))
        result = popup.exec_()

        if result == QDialog.Accepted:
            with self._editor:
                self._editor.major_items_configuration = major_items_configuration.replace_state_for_item(
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
        self.energy_tank_shuffled_spinbox.setMaximum(DEFAULT_MAXIMUM_SHUFFLED[-1])
        self.energy_tank_shuffled_spinbox.valueChanged.connect(self._on_update_shuffled_energy_tank)

        category_layout.addWidget(starting_label, 0, 0)
        category_layout.addWidget(self.energy_tank_starting_spinbox, 0, 1)
        category_layout.addWidget(shuffled_label, 1, 0)
        category_layout.addWidget(self.energy_tank_shuffled_spinbox, 1, 1)

    def _on_update_starting_energy_tank(self, value: int):
        with self._editor as options:
            major_configuration = options.major_items_configuration
            options.major_items_configuration = major_configuration.replace_state_for_item(
                self._energy_tank_item,
                dataclasses.replace(major_configuration.items_state[self._energy_tank_item],
                                    num_included_in_starting_items=value)
            )

    def _on_update_shuffled_energy_tank(self, value: int):
        with self._editor as options:
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

        resource_database = default_database.resource_database_for(self.game)

        for ammo in item_database.ammo.values():
            title_layout = QHBoxLayout()
            title_layout.setObjectName(f"{ammo.name} Title Horizontal Layout")

            expand_ammo_button = QToolButton(self.ammo_box)
            expand_ammo_button.setGeometry(QRect(20, 30, 24, 21))
            expand_ammo_button.setText("+")
            title_layout.addWidget(expand_ammo_button)

            category_label = QLabel(self.ammo_box)
            category_label.setSizePolicy(size_policy)
            category_label.setText(ammo.name + "s")
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

            if ammo.temporaries:
                require_major_item_check = QCheckBox(pickup_box)
                require_major_item_check.setText("Requires the major item to work?")
                require_major_item_check.stateChanged.connect(partial(self._on_update_ammo_require_major_item, ammo))
                layout.addWidget(require_major_item_check, current_row, 0, 1, 2)
                current_row += 1
            else:
                require_major_item_check = None

            expected_count = QLabel(pickup_box)
            expected_count.setWordWrap(True)
            expected_count.setText(_EXPECTED_COUNT_TEXT_TEMPLATE)
            expected_count.setToolTip("Some expansions may provide 1 extra, even with no variance, if the total count "
                                      "is not divisible by the pickup count.")
            layout.addWidget(expected_count, current_row, 0, 1, 2)
            current_row += 1

            self._ammo_pickup_widgets[ammo] = (pickup_spinbox, expected_count, expand_ammo_button,
                                               category_label, pickup_box, require_major_item_check)

            expand_ammo_button.clicked.connect(partial(_toggle_box_visibility, expand_ammo_button, pickup_box))
            pickup_box.setVisible(False)

            self.ammo_layout.addLayout(title_layout)
            self.ammo_layout.addWidget(pickup_box)

    def _on_update_ammo_maximum_spinbox(self, ammo_int: int, value: int):
        with self._editor as options:
            options.ammo_configuration = options.ammo_configuration.replace_maximum_for_item(
                ammo_int, value
            )

    def _on_update_ammo_pickup_spinbox(self, ammo: Ammo, value: int):
        with self._editor as options:
            ammo_configuration = options.ammo_configuration
            options.ammo_configuration = ammo_configuration.replace_state_for_ammo(
                ammo,
                dataclasses.replace(ammo_configuration.items_state[ammo], pickup_count=value)
            )

    def _on_update_ammo_require_major_item(self, ammo: Ammo, value: int):
        with self._editor as options:
            ammo_configuration = options.ammo_configuration
            options.ammo_configuration = ammo_configuration.replace_state_for_ammo(
                ammo,
                dataclasses.replace(ammo_configuration.items_state[ammo], requires_major_item=bool(value))
            )
