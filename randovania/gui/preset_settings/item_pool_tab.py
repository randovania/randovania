from __future__ import annotations

import collections
import dataclasses
from functools import partial
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtWidgets

import randovania.gui.lib.signal_handling
from randovania.exporter import item_names
from randovania.game_description import default_database
from randovania.game_description.resources.resource_type import ResourceType
from randovania.games.game import RandovaniaGame
from randovania.generator.pickup_pool import pool_creator
from randovania.gui.generated.preset_item_pool_ui import Ui_PresetItemPool
from randovania.gui.lib import common_qt_lib
from randovania.gui.lib.foldable import Foldable
from randovania.gui.lib.scroll_protected import ScrollProtectedComboBox, ScrollProtectedSpinBox
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.gui.preset_settings.progressive_item_widget import ProgressiveItemWidget
from randovania.gui.preset_settings.split_ammo_widget import AmmoPickupWidgets
from randovania.gui.preset_settings.standard_pickup_widget import StandardPickupWidget
from randovania.layout.base.available_locations import RandomizationMode
from randovania.layout.base.standard_pickup_state import StandardPickupState
from randovania.layout.exceptions import InvalidConfiguration

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.pickup.ammo_pickup import AmmoPickupDefinition
    from randovania.game_description.pickup.pickup_category import PickupCategory
    from randovania.game_description.pickup.pickup_database import PickupDatabase
    from randovania.game_description.pickup.standard_pickup import StandardPickupDefinition
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


def _create_separator(parent: QtWidgets.QWidget) -> QtWidgets.QFrame:
    separator_line = QtWidgets.QFrame(parent)
    separator_line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
    separator_line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
    transparent = QtWidgets.QGraphicsOpacityEffect(separator_line)
    transparent.setOpacity(0.33)
    separator_line.setGraphicsEffect(transparent)
    return separator_line


def _format_expected_counts(
    ammo: AmmoPickupDefinition,
    template: str,
    ammo_provided: dict[str, int],
    item_for_index: dict[str, ItemResourceInfo],
    self_counts: list[int],
) -> str:
    try:
        return template.format(
            total=" and ".join(
                item_names.add_quantity_to_resource(item_for_index[ammo_index].long_name, self_count, True)
                for ammo_index, self_count in zip(ammo.items, self_counts)
            ),
            from_items=" and ".join(
                item_names.add_quantity_to_resource(
                    item_for_index[ammo_index].long_name, ammo_provided[ammo_index] - self_count, True
                )
                for ammo_index, self_count in zip(ammo.items, self_counts)
            ),
            maximum=" and ".join(
                item_names.add_quantity_to_resource(
                    item_for_index[ammo_index].long_name,
                    min(ammo_provided[ammo_index], item_for_index[ammo_index].max_capacity),
                    True,
                )
                for ammo_index in ammo.items
            ),
        )
    except InvalidConfiguration as invalid_config:
        return str(invalid_config)


class PresetItemPool(PresetTab, Ui_PresetItemPool):
    game: RandovaniaGame
    _boxes_for_category: dict[
        str, tuple[QtWidgets.QGroupBox, QtWidgets.QGridLayout, dict[StandardPickupDefinition, StandardPickupWidget]]
    ]
    _default_pickups: dict[PickupCategory, QtWidgets.QComboBox]

    _ammo_item_count_spinboxes: dict[str, list[QtWidgets.QSpinBox]]
    _ammo_pickup_widgets: dict[AmmoPickupDefinition, AmmoPickupWidgets]

    _progressive_widgets: list[ProgressiveItemWidget]

    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        self.item_pool_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

        # Relevant Items
        self.game = editor.game
        self.game_description = default_database.game_description_for(self.game)
        pickup_database = default_database.pickup_database_for_game(self.game)

        self._register_random_starting_events()
        self._create_categories_boxes(pickup_database, size_policy)
        self._create_customizable_default_items(pickup_database)
        self._create_standard_pickup_boxes(pickup_database, self.game_description.resource_database)
        self._create_progressive_widgets(pickup_database)
        self._create_ammo_pickup_boxes(size_policy, pickup_database)

    @classmethod
    def tab_title(cls) -> str:
        return "Item Pool"

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return False

    def on_preset_changed(self, preset: Preset):
        layout = preset.configuration
        major_configuration = layout.standard_pickup_configuration

        # Random Starting Pickups
        self.minimum_starting_spinbox.setValue(major_configuration.minimum_random_starting_pickups)
        self.maximum_starting_spinbox.setValue(major_configuration.maximum_random_starting_pickups)

        # Default Pickups
        for category, default_item in major_configuration.default_pickups.items():
            randovania.gui.lib.signal_handling.set_combo_with_value(self._default_pickups[category], default_item)

            for item, widget in self._boxes_for_category[category.name][2].items():
                widget.setEnabled(default_item != item)

        # Standard Pickups
        for _, _, elements in self._boxes_for_category.values():
            for standard_pickup, widget in elements.items():
                widget.set_new_state(major_configuration.pickups_state[standard_pickup])

        # Progressive Items
        for progressive_widget in self._progressive_widgets:
            progressive_widget.on_preset_changed(
                preset,
                self._boxes_for_category[progressive_widget.progressive_item.pickup_category.name][2],
            )

        # Ammo
        ammo_configuration = layout.ammo_pickup_configuration

        ammo_provided = major_configuration.calculate_provided_ammo()
        for ammo, state in ammo_configuration.pickups_state.items():
            for ammo_index, count in enumerate(state.ammo_count):
                if ammo.items[ammo_index] in ammo_provided:
                    ammo_provided[ammo.items[ammo_index]] += count * state.pickup_count
                else:
                    ammo_provided[ammo.items[ammo_index]] = count * state.pickup_count

        resource_database = self.game_description.resource_database

        item_for_index: dict[str, ItemResourceInfo] = {
            ammo_index: resource_database.get_item(ammo_index) for ammo_index in ammo_provided.keys()
        }

        for ammo, state in ammo_configuration.pickups_state.items():
            widgets = self._ammo_pickup_widgets[ammo]
            widgets.pickup_spinbox.setValue(state.pickup_count)

            if widgets.require_main_item_check is not None:
                widgets.require_main_item_check.setChecked(state.requires_main_item)
                if self.game == RandovaniaGame.METROID_PRIME:
                    widgets.require_main_item_check.setChecked(False)

            self_counts = []
            for ammo_index, count in enumerate(state.ammo_count):
                self_counts.append(count * state.pickup_count)
                self._ammo_item_count_spinboxes[ammo.name][ammo_index].setValue(count)

            if widgets.expected_count is not None:
                if state.pickup_count == 0:
                    widgets.expected_count.setText("No expansions will be created.")
                else:
                    widgets.expected_count.setText(
                        _format_expected_counts(
                            ammo, widgets.expected_template, ammo_provided, item_for_index, self_counts
                        )
                    )

        # Item pool count
        try:
            per_category_pool = pool_creator.calculate_pool_pickup_count(layout)
            pool_items, maximum_size = pool_creator.get_total_pickup_count(per_category_pool)
            message = f"Items in pool: {pool_items}/{maximum_size}"
            common_qt_lib.set_error_border_stylesheet(self.item_pool_count_label, pool_items > maximum_size)

            if layout.available_locations.randomization_mode is not RandomizationMode.FULL:
                parts = []
                for category, (count, num_nodes) in per_category_pool.items():
                    if isinstance(category, str):
                        if num_nodes > 0:
                            parts.append(f"{category}: {num_nodes}")
                    else:
                        parts.append(f"{category.long_name}: {count}/{num_nodes}")

                message += "<br />"
                message += " - ".join(parts)

            self.item_pool_count_label.setText(message)
            self.item_pool_description_label.setText(
                f"If there are fewer than {maximum_size} items, the rest of the "
                f"item locations will contain 'Nothing' items."
            )

        except InvalidConfiguration as invalid_config:
            self.item_pool_count_label.setText(f"Invalid Configuration: {invalid_config}")
            common_qt_lib.set_error_border_stylesheet(self.item_pool_count_label, True)

    # Random Starting
    def _register_random_starting_events(self):
        self.minimum_starting_spinbox.valueChanged.connect(self._on_update_minimum_starting)
        self.maximum_starting_spinbox.valueChanged.connect(self._on_update_maximum_starting)

    def _on_update_minimum_starting(self, value: int):
        with self._editor as options:
            options.standard_pickup_configuration = dataclasses.replace(
                options.standard_pickup_configuration, minimum_random_starting_pickups=value
            )

    def _on_update_maximum_starting(self, value: int):
        with self._editor as options:
            options.standard_pickup_configuration = dataclasses.replace(
                options.standard_pickup_configuration, maximum_random_starting_pickups=value
            )

    def _create_categories_boxes(self, pickup_database: PickupDatabase, size_policy):
        self._boxes_for_category = {}
        all_categories = list(pickup_database.pickup_categories.values())

        categories = set()
        standard_broad_categories = set()
        for standard_pickup in pickup_database.standard_pickups.values():
            if not standard_pickup.hide_from_gui:
                categories.add(standard_pickup.pickup_category)
                standard_broad_categories.add(standard_pickup.broad_category.name)

        for ammo_pickup in pickup_database.ammo_pickups.values():
            # When a proper distinction between UI and hint categories exists, this needs to be changed
            if ammo_pickup.broad_category.name in standard_broad_categories:
                continue
            categories.add(ammo_pickup.broad_category)

        for standard_pickup_category in sorted(categories, key=lambda it: all_categories.index(it)):
            category_box = Foldable(None, standard_pickup_category.long_name)
            category_box.setObjectName(f"category_box {standard_pickup_category}")
            category_layout = QtWidgets.QGridLayout()
            category_layout.setObjectName(f"category_layout {standard_pickup_category}")
            category_box.set_content_layout(category_layout)

            self.item_pool_layout.addWidget(category_box)
            self._boxes_for_category[standard_pickup_category.name] = category_box, category_layout, {}

    def _create_customizable_default_items(self, pickup_database: PickupDatabase):
        self._default_pickups = {}

        for category, possibilities in pickup_database.default_pickups.items():
            parent, layout, _ = self._boxes_for_category[category.name]

            label = QtWidgets.QLabel(parent)
            label.setText(f"Default {category.long_name}")
            layout.addWidget(label, 0, 0)

            combo = ScrollProtectedComboBox(parent)
            for pickup in possibilities:
                combo.addItem(pickup.name, pickup)
            combo.currentIndexChanged.connect(partial(self._on_default_pickup_updated, category, combo))
            layout.addWidget(combo, 0, 1)

            if len(possibilities) <= 1:
                label.hide()
                combo.hide()

            self._default_pickups[category] = combo

    def _on_default_pickup_updated(self, category: PickupCategory, combo: QtWidgets.QComboBox, _):
        pickup: StandardPickupDefinition = combo.currentData()
        with self._editor as editor:
            new_config = editor.standard_pickup_configuration
            new_config = new_config.replace_default_pickup(category, pickup)
            new_config = new_config.replace_state_for_pickup(
                pickup,
                StandardPickupState(
                    num_included_in_starting_pickups=1, included_ammo=new_config.pickups_state[pickup].included_ammo
                ),
            )
            editor.standard_pickup_configuration = new_config

    def _create_standard_pickup_boxes(self, pickup_database: PickupDatabase, resource_database: ResourceDatabase):
        for standard_pickup in pickup_database.standard_pickups.values():
            if standard_pickup.hide_from_gui or standard_pickup.pickup_category.name == "energy_tank":
                continue

            category_box, category_layout, elements = self._boxes_for_category[standard_pickup.pickup_category.name]
            widget = StandardPickupWidget(None, standard_pickup, StandardPickupState(), resource_database)
            widget.Changed.connect(partial(self._on_standard_pickup_updated, widget))

            row = category_layout.rowCount()
            if row > 1:
                # Show the transparent separator line if it's not the first element
                widget.separator_line.show()

            category_layout.addWidget(widget, row, 0, 1, 2)
            elements[standard_pickup] = widget

    def _on_standard_pickup_updated(self, pickup_widget: StandardPickupWidget):
        with self._editor as editor:
            editor.standard_pickup_configuration = editor.standard_pickup_configuration.replace_state_for_pickup(
                pickup_widget.pickup, pickup_widget.state
            )

    # Ammo
    def _create_ammo_pickup_boxes(self, size_policy, pickup_database: PickupDatabase):
        """
        Creates the GroupBox with SpinBoxes for selecting the pickup count of all the ammo
        :param pickup_database:
        :return:
        """

        self._ammo_item_count_spinboxes = collections.defaultdict(list)
        self._ammo_pickup_widgets = {}

        resource_database = default_database.resource_database_for(self.game)
        broad_to_category = {
            "beam_related": "beam",
            "morph_ball_related": "morph_ball",
            "missile_related": "missile",
        }

        layouts_with_lines: set[tuple[Foldable, QtWidgets.QGridLayout]] = {
            self._boxes_for_category[broad_to_category.get(ammo.broad_category.name, ammo.broad_category.name)][:2]
            for ammo in pickup_database.ammo_pickups.values()
        }

        for box, layout in layouts_with_lines:
            layout.addWidget(_create_separator(box), layout.rowCount(), 0, 1, -1)

        for ammo in pickup_database.ammo_pickups.values():
            category_box, category_layout, _ = self._boxes_for_category[
                broad_to_category.get(ammo.broad_category.name, ammo.broad_category.name)
            ]

            pickup_box = QtWidgets.QGroupBox(category_box)
            pickup_box.setSizePolicy(size_policy)
            pickup_box.setTitle(ammo.name + "s")
            layout = QtWidgets.QGridLayout(pickup_box)
            layout.setObjectName(f"{ammo.name} Box Layout")

            current_row = 0

            if ammo.description is not None:
                description_label = QtWidgets.QLabel(ammo.description, pickup_box)
                description_label.setWordWrap(True)
                layout.addWidget(description_label, current_row, 0, 1, -1)
                current_row += 1

            current_column = 0

            def add_column(widget: QtWidgets.QWidget) -> None:
                nonlocal current_column
                layout.addWidget(widget, current_row, current_column)
                current_column += 1

            for ammo_index, ammo_item in enumerate(ammo.items):
                item = resource_database.get_by_type_and_index(ResourceType.ITEM, ammo_item)
                minimum_count = -item.max_capacity if ammo.allows_negative else 0

                item_count_spinbox = ScrollProtectedSpinBox(pickup_box)
                item_count_spinbox.setMinimum(minimum_count)
                item_count_spinbox.setMaximum(item.max_capacity)
                item_count_spinbox.setSuffix(f" {item.long_name}")
                item_count_spinbox.valueChanged.connect(
                    partial(self._on_update_ammo_pickup_item_count_spinbox, ammo, ammo_index)
                )
                self._ammo_item_count_spinboxes[ammo.name].append(item_count_spinbox)
                add_column(item_count_spinbox)

            # Pickup Count
            pickup_spinbox = ScrollProtectedSpinBox(pickup_box)
            pickup_spinbox.setMaximum(999)
            pickup_spinbox.valueChanged.connect(partial(self._on_update_ammo_pickup_num_count_spinbox, ammo))
            pickup_spinbox.setSuffix(" pickups")
            pickup_spinbox.setToolTip("How many instances of this expansion should be placed.")

            add_column(pickup_spinbox)
            current_row += 1

            # FIXME: hardcoded check to hide required mains for Prime 1
            if ammo.temporary:
                require_main_item_check = QtWidgets.QCheckBox(pickup_box)
                require_main_item_check.setText("Requires the main item to work?")
                require_main_item_check.stateChanged.connect(partial(self._on_update_ammo_require_main_item, ammo))
                if self.game == RandovaniaGame.METROID_PRIME:
                    require_main_item_check.setVisible(False)
                layout.addWidget(require_main_item_check, current_row, 0, 1, -1)
                current_row += 1
            else:
                require_main_item_check = None

            template_entries = []

            if ammo.include_expected_counts:
                template_entries.append("For a total of {total} from this source.")

            if ammo.explain_other_sources:
                template_entries.append("{from_items} will be provided from other sources.")

            if ammo.mention_limit:
                template_entries.append("{maximum} is the maximum you can have at once.")

            expected_template = "\n".join(template_entries)

            if expected_template:
                expected_count = QtWidgets.QLabel(pickup_box)
                expected_count.setWordWrap(True)
                expected_count.setText("<TODO>")
                layout.addWidget(expected_count, current_row, 0, 1, -1)
                current_row += 1
            else:
                expected_count = None

            self._ammo_pickup_widgets[ammo] = AmmoPickupWidgets(
                pickup_spinbox, expected_count, expected_template, pickup_box, require_main_item_check
            )
            category_layout.addWidget(pickup_box)

    def _on_update_ammo_pickup_item_count_spinbox(self, ammo: AmmoPickupDefinition, ammo_index: int, value: int):
        with self._editor as options:
            ammo_configuration = options.ammo_pickup_configuration
            state = ammo_configuration.pickups_state[ammo]
            ammo_count = list(state.ammo_count)
            ammo_count[ammo_index] = value

            options.ammo_pickup_configuration = ammo_configuration.replace_state_for_ammo(
                ammo, dataclasses.replace(state, ammo_count=tuple(ammo_count))
            )

    def _on_update_ammo_pickup_num_count_spinbox(self, ammo: AmmoPickupDefinition, value: int):
        with self._editor as options:
            ammo_configuration = options.ammo_pickup_configuration
            options.ammo_pickup_configuration = ammo_configuration.replace_state_for_ammo(
                ammo, dataclasses.replace(ammo_configuration.pickups_state[ammo], pickup_count=value)
            )

    def _on_update_ammo_require_main_item(self, ammo: AmmoPickupDefinition, value: int):
        with self._editor as options:
            ammo_configuration = options.ammo_pickup_configuration
            options.ammo_pickup_configuration = ammo_configuration.replace_state_for_ammo(
                ammo, dataclasses.replace(ammo_configuration.pickups_state[ammo], requires_main_item=bool(value))
            )

    def _create_progressive_widgets(self, pickup_database: PickupDatabase):
        self._progressive_widgets = []

        all_progressive = list(self.game.gui.progressive_item_gui_tuples)

        layouts_with_lines: set[tuple[Foldable, QtWidgets.QGridLayout]] = {
            self._boxes_for_category[pickup_database.standard_pickups[progressive_item_name].pickup_category.name][:2]
            for progressive_item_name, non_progressive_items in all_progressive
        }

        for box, layout in layouts_with_lines:
            layout.addWidget(_create_separator(box), layout.rowCount(), 0, 1, -1)

        for progressive_item_name, non_progressive_items in all_progressive:
            progressive_item = pickup_database.standard_pickups[progressive_item_name]
            parent, layout, _ = self._boxes_for_category[progressive_item.pickup_category.name]

            widget = ProgressiveItemWidget(
                parent,
                self._editor,
                progressive_item=progressive_item,
                non_progressive_items=[pickup_database.standard_pickups[it] for it in non_progressive_items],
            )
            widget.setText("Use progressive {}".format(" → ".join(non_progressive_items)))
            self._progressive_widgets.append(widget)
            layout.addWidget(widget, layout.rowCount(), 0, 1, -1)
