import collections
import dataclasses
import functools
from functools import partial
from typing import Dict, Tuple, List

from PySide2 import QtWidgets, QtCore

from randovania.game_description import default_database
from randovania.game_description.item.ammo import Ammo
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.item.item_database import ItemDatabase
from randovania.game_description.item.major_item import MajorItem
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_type import ResourceType
from randovania.games.game import RandovaniaGame
from randovania.generator.item_pool import pool_creator
from randovania.generator.item_pool.ammo import items_for_ammo
from randovania.gui.generated.preset_item_pool_ui import Ui_PresetItemPool
from randovania.gui.lib import common_qt_lib, signal_handling
from randovania.gui.lib.scroll_protected import ScrollProtectedComboBox, ScrollProtectedSpinBox
from randovania.gui.preset_settings.item_configuration_widget import ItemConfigurationWidget
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.gui.preset_settings.progressive_item_widget import ProgressiveItemWidget
from randovania.gui.preset_settings.split_ammo_widget import SplitAmmoWidget, AmmoPickupWidgets
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.base.ammo_state import AmmoState
from randovania.layout.base.major_item_state import ENERGY_TANK_MAXIMUM_COUNT, DEFAULT_MAXIMUM_SHUFFLED, MajorItemState
from randovania.layout.base.pickup_model import PickupModelDataSource, PickupModelStyle
from randovania.layout.preset import Preset
from randovania.lib.enum_lib import iterate_enum
from randovania.resolver.exceptions import InvalidConfiguration

_EXPECTED_COUNT_TEXT_TEMPLATE = ("Each expansion will provide, on average, {per_expansion}, for a total of {total}."
                                 "\n{from_items} will be provided from major items.")
_EXPECTED_COUNT_TEXT_TEMPLATE_EXACT = ("Each expansion will provide exactly {per_expansion}, for a total of {total}."
                                       "\n{from_items} will be provided from major items.")


class PresetItemPool(PresetTab, Ui_PresetItemPool):
    _boxes_for_category: Dict[ItemCategory, Tuple[QtWidgets.QGroupBox, QtWidgets.QGridLayout,
                                                  Dict[MajorItem, ItemConfigurationWidget]]]
    _default_items: Dict[ItemCategory, QtWidgets.QComboBox]

    _ammo_maximum_spinboxes: Dict[int, List[QtWidgets.QSpinBox]]
    _ammo_pickup_widgets: Dict[Ammo, AmmoPickupWidgets]
    _progressive_widgets: List[ProgressiveItemWidget]
    _split_ammo_widgets: List[SplitAmmoWidget]

    def __init__(self, editor: PresetEditor):
        super().__init__()
        self.setupUi(self)

        self._editor = editor
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        self.item_pool_layout.setAlignment(QtCore.Qt.AlignTop)

        # Relevant Items
        self.game = editor.game
        self.game_description = default_database.game_description_for(self.game)
        item_database = default_database.item_database_for_game(self.game)

        self._energy_tank_item = item_database.major_items["Energy Tank"]

        self._setup_general_widgets()
        self._register_random_starting_events()
        self._create_categories_boxes(item_database, size_policy)
        self._create_customizable_default_items(item_database)
        self._create_progressive_widgets(item_database)
        self._create_major_item_boxes(item_database, self.game_description.resource_database)
        self._create_energy_tank_box()
        self._create_split_ammo_widgets(item_database)
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

        # General
        self.pickup_model_combo.setCurrentIndex(self.pickup_model_combo.findData(layout.pickup_model_style))
        self.pickup_data_source_combo.setCurrentIndex(
            self.pickup_data_source_combo.findData(layout.pickup_model_data_source))
        self.pickup_data_source_combo.setEnabled(layout.pickup_model_style != PickupModelStyle.ALL_VISIBLE)

        self.multi_pickup_placement_check.setChecked(layout.multi_pickup_placement)

        # Random Starting Items
        self.minimum_starting_spinbox.setValue(major_configuration.minimum_random_starting_items)
        self.maximum_starting_spinbox.setValue(major_configuration.maximum_random_starting_items)

        # Default Items
        for category, default_item in major_configuration.default_items.items():
            combo = self._default_items[category]
            combo.setCurrentIndex(combo.findData(default_item))

            for item, widget in self._boxes_for_category[category][2].items():
                widget.setEnabled(default_item != item)

        # Major Items
        for _, _, elements in self._boxes_for_category.values():
            for major_item, widget in elements.items():
                widget.state = major_configuration.items_state[major_item]

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
        resource_database = self.game_description.resource_database

        item_for_index: Dict[int, ItemResourceInfo] = {
            ammo_index: resource_database.get_item(ammo_index)
            for ammo_index in ammo_provided.keys()
        }

        for ammo, state in ammo_configuration.items_state.items():
            widgets = self._ammo_pickup_widgets[ammo]
            widgets.pickup_spinbox.setValue(state.pickup_count)

            if widgets.require_major_item_check is not None:
                widgets.require_major_item_check.setChecked(state.requires_major_item)

            try:
                if state.pickup_count == 0:
                    widgets.expected_count.setText("No expansions will be created.")
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

                widgets.expected_count.setText(
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
                widgets.expected_count.setText(str(invalid_config))

        # Item pool count
        try:
            pool_items, maximum_size = pool_creator.calculate_pool_item_count(layout)
            self.item_pool_count_label.setText("Items in pool: {}/{}".format(pool_items, maximum_size))
            common_qt_lib.set_error_border_stylesheet(self.item_pool_count_label, pool_items > maximum_size)

        except InvalidConfiguration as invalid_config:
            self.item_pool_count_label.setText("Invalid Configuration: {}".format(invalid_config))
            common_qt_lib.set_error_border_stylesheet(self.item_pool_count_label, True)

    # General

    def _setup_general_widgets(self):
        # Item Data
        for i, value in enumerate(PickupModelStyle):
            self.pickup_model_combo.setItemData(i, value)
        for i, value in enumerate(PickupModelDataSource):
            self.pickup_data_source_combo.setItemData(i, value)

        # TODO: implement the LOCATION data source
        self.pickup_data_source_combo.removeItem(self.pickup_data_source_combo.findData(PickupModelDataSource.LOCATION))
        self.pickup_model_combo.currentIndexChanged.connect(
            self._persist_enum(self.pickup_model_combo, "pickup_model_style"))
        self.pickup_data_source_combo.currentIndexChanged.connect(
            self._persist_enum(self.pickup_data_source_combo, "pickup_model_data_source"))

        signal_handling.on_checked(self.multi_pickup_placement_check, self._persist_multi_pickup_placement)

    def _persist_enum(self, combo: QtWidgets.QComboBox, attribute_name: str):
        def persist(index: int):
            with self._editor as options:
                options.set_configuration_field(attribute_name, combo.itemData(index))

        return persist

    def _persist_multi_pickup_placement(self, value: bool):
        with self._editor as editor:
            editor.set_configuration_field("multi_pickup_placement", value)

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

        if self.game == RandovaniaGame.METROID_PRIME_ECHOES:
            all_progressive.append((
                "Progressive Suit",
                ("Dark Suit", "Light Suit"),
            ))
            all_progressive.append((
                "Progressive Grapple",
                ("Grapple Beam", "Screw Attack"),
            ))
        elif self.game == RandovaniaGame.METROID_PRIME_CORRUPTION:
            all_progressive.append((
                "Progressive Missile",
                ("Ice Missile", "Seeker Missile"),
            ))
            all_progressive.append((
                "Progressive Beam",
                ("Plasma Beam", "Nova Beam"),
            ))

        for (progressive_item_name, non_progressive_items) in all_progressive:
            progressive_item = item_database.major_items[progressive_item_name]
            parent, layout, _ = self._boxes_for_category[progressive_item.item_category]

            widget = ProgressiveItemWidget(
                parent, self._editor,
                progressive_item=progressive_item,
                non_progressive_items=[item_database.major_items[it] for it in non_progressive_items],
            )
            widget.setText("Use progressive {}".format(" → ".join(non_progressive_items)))
            self._progressive_widgets.append(widget)
            layout.addWidget(widget)

    def _create_split_ammo_widgets(self, item_database: ItemDatabase):
        parent, layout, _ = self._boxes_for_category[ItemCategory.BEAM]

        self._split_ammo_widgets = []

        if self.game == RandovaniaGame.METROID_PRIME_ECHOES:
            beam_ammo = SplitAmmoWidget(
                parent, self._editor,
                unified_ammo=item_database.ammo["Beam Ammo Expansion"],
                split_ammo=[
                    item_database.ammo["Dark Ammo Expansion"],
                    item_database.ammo["Light Ammo Expansion"],
                ],
            )
            beam_ammo.setText("Split Beam Ammo Expansions")
            self._split_ammo_widgets.append(beam_ammo)

        if self._split_ammo_widgets:
            line = QtWidgets.QFrame(parent)
            line.setFrameShape(QtWidgets.QFrame.HLine)
            line.setFrameShadow(QtWidgets.QFrame.Sunken)
            layout.addWidget(line, layout.rowCount(), 0, 1, -1)

        for widget in self._split_ammo_widgets:
            layout.addWidget(widget, layout.rowCount(), 0, 1, -1)

    def _create_categories_boxes(self, item_database: ItemDatabase, size_policy):
        self._boxes_for_category = {}

        categories = set()
        for major_item in item_database.major_items.values():
            if not major_item.required:
                categories.add(major_item.item_category)

        all_categories = list(iterate_enum(ItemCategory))
        for major_item_category in sorted(categories, key=lambda it: all_categories.index(it)):
            category_box = QtWidgets.QGroupBox(self.scroll_area_contents)
            category_box.setTitle(major_item_category.long_name)
            category_box.setSizePolicy(size_policy)
            category_box.setObjectName(f"category_box {major_item_category}")

            category_layout = QtWidgets.QGridLayout(category_box)
            category_layout.setObjectName(f"category_layout {major_item_category}")

            self.item_pool_layout.addWidget(category_box)
            self._boxes_for_category[major_item_category] = category_box, category_layout, {}

    def _create_customizable_default_items(self, item_database: ItemDatabase):
        self._default_items = {}

        for category, possibilities in item_database.default_items.items():
            parent, layout, _ = self._boxes_for_category[category]

            label = QtWidgets.QLabel(parent)
            label.setText(f"Default {category.long_name}")
            layout.addWidget(label, 0, 0)

            combo = ScrollProtectedComboBox(parent)
            for item in possibilities:
                combo.addItem(item.name, item)
            combo.currentIndexChanged.connect(partial(self._on_default_item_updated, category, combo))
            layout.addWidget(combo, 0, 1)

            self._default_items[category] = combo

    def _on_default_item_updated(self, category: ItemCategory, combo: QtWidgets.QComboBox, _):
        with self._editor as editor:
            new_config = editor.major_items_configuration
            new_config = new_config.replace_default_item(category, combo.currentData())
            new_config = new_config.replace_state_for_item(combo.currentData(),
                                                           MajorItemState(num_included_in_starting_items=1))
            editor.major_items_configuration = new_config

    def _create_major_item_boxes(self, item_database: ItemDatabase, resource_database: ResourceDatabase):
        for major_item in item_database.major_items.values():
            if major_item.required or major_item.item_category == ItemCategory.ENERGY_TANK:
                continue

            category_box, category_layout, elements = self._boxes_for_category[major_item.item_category]
            widget = ItemConfigurationWidget(None, major_item, MajorItemState(), resource_database)
            widget.Changed.connect(partial(self._on_major_item_updated, widget))

            row = category_layout.rowCount()
            category_layout.addWidget(widget, row, 0, 1, -1)

            elements[major_item] = widget

    def _on_major_item_updated(self, item_widget: ItemConfigurationWidget):
        with self._editor as editor:
            editor.major_items_configuration = editor.major_items_configuration.replace_state_for_item(
                item_widget.item, item_widget.state
            )

    # Energy Tank

    def _create_energy_tank_box(self):
        category_box, category_layout, _ = self._boxes_for_category[ItemCategory.ENERGY_TANK]

        starting_label = QtWidgets.QLabel(category_box)
        starting_label.setText("Starting Quantity")

        shuffled_label = QtWidgets.QLabel(category_box)
        shuffled_label.setText("Shuffled Quantity")

        self.energy_tank_starting_spinbox = ScrollProtectedSpinBox(category_box)
        self.energy_tank_starting_spinbox.setMaximum(ENERGY_TANK_MAXIMUM_COUNT)
        self.energy_tank_starting_spinbox.valueChanged.connect(self._on_update_starting_energy_tank)
        self.energy_tank_shuffled_spinbox = ScrollProtectedSpinBox(category_box)
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
        broad_to_category = {
            ItemCategory.BEAM_RELATED: ItemCategory.BEAM,
            ItemCategory.MORPH_BALL_RELATED: ItemCategory.MORPH_BALL,
            ItemCategory.MISSILE_RELATED: ItemCategory.MISSILE,
        }

        for ammo in item_database.ammo.values():
            category_box, category_layout, _ = self._boxes_for_category[broad_to_category[ammo.broad_category]]

            pickup_box = QtWidgets.QGroupBox(category_box)
            pickup_box.setSizePolicy(size_policy)
            pickup_box.setTitle(ammo.name + "s")
            layout = QtWidgets.QGridLayout(pickup_box)
            layout.setObjectName(f"{ammo.name} Box Layout")
            current_row = 0

            for ammo_item in ammo.items:
                item = resource_database.get_by_type_and_index(ResourceType.ITEM, ammo_item)

                target_count_label = QtWidgets.QLabel(pickup_box)
                target_count_label.setText(f"{item.long_name} Target" if len(ammo.items) > 1 else "Target count")

                maximum_spinbox = ScrollProtectedSpinBox(pickup_box)
                maximum_spinbox.setMaximum(ammo.maximum)
                maximum_spinbox.valueChanged.connect(partial(self._on_update_ammo_maximum_spinbox, ammo_item))
                self._ammo_maximum_spinboxes[ammo_item].append(maximum_spinbox)

                layout.addWidget(target_count_label, current_row, 0)
                layout.addWidget(maximum_spinbox, current_row, 1)
                current_row += 1

            count_label = QtWidgets.QLabel(pickup_box)
            count_label.setText("Pickup Count")
            count_label.setToolTip("How many instances of this expansion should be placed.")

            pickup_spinbox = ScrollProtectedSpinBox(pickup_box)
            pickup_spinbox.setMaximum(AmmoState.maximum_pickup_count())
            pickup_spinbox.valueChanged.connect(partial(self._on_update_ammo_pickup_spinbox, ammo))

            layout.addWidget(count_label, current_row, 0)
            layout.addWidget(pickup_spinbox, current_row, 1)
            current_row += 1

            if ammo.temporary:
                require_major_item_check = QtWidgets.QCheckBox(pickup_box)
                require_major_item_check.setText("Requires the major item to work?")
                require_major_item_check.stateChanged.connect(partial(self._on_update_ammo_require_major_item, ammo))
                layout.addWidget(require_major_item_check, current_row, 0, 1, 2)
                current_row += 1
            else:
                require_major_item_check = None

            expected_count = QtWidgets.QLabel(pickup_box)
            expected_count.setWordWrap(True)
            expected_count.setText(_EXPECTED_COUNT_TEXT_TEMPLATE)
            expected_count.setToolTip("Some expansions may provide 1 extra, even with no variance, if the total count "
                                      "is not divisible by the pickup count.")
            layout.addWidget(expected_count, current_row, 0, 1, 2)
            current_row += 1

            self._ammo_pickup_widgets[ammo] = AmmoPickupWidgets(pickup_spinbox, expected_count,
                                                                pickup_box, require_major_item_check)
            category_layout.addWidget(pickup_box)

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
