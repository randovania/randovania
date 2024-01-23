from __future__ import annotations

import collections
import functools
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui, QtWidgets

from randovania.exporter import item_names
from randovania.game_description.db.pickup_node import PickupNode
from randovania.gui.game_details.game_details_tab import GameDetailsTab
from randovania.gui.generated.pickup_details_tab_ui import Ui_PickupDetailsTab
from randovania.gui.lib import signal_handling
from randovania.layout import filtered_database

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
    from randovania.games.game import RandovaniaGame
    from randovania.interface_common.players_configuration import PlayersConfiguration
    from randovania.layout.base.base_configuration import BaseConfiguration


def _show_pickup_spoiler(button: QtWidgets.QPushButton):
    target_player = getattr(button, "target_player", None)
    if target_player is not None:
        label = f"{button.item_name} for {button.player_names[target_player]}"
    else:
        label = button.item_name
    button.setText(label)
    button.item_is_hidden = False


def _hide_pickup_spoiler(button: QtWidgets.QPushButton):
    button.setText("Hidden")
    button.item_is_hidden = True


class PickupDetailsTab(GameDetailsTab, Ui_PickupDetailsTab):
    pickup_spoiler_buttons: list[QtWidgets.QPushButton]

    def __init__(self, parent: QtWidgets.QWidget, game: RandovaniaGame):
        super().__init__(parent, game)
        self.root = QtWidgets.QWidget(parent)
        self.setupUi(self.root)

        self.pickup_spoiler_buttons = []
        self._pickup_spoiler_region_to_group = {}

        self.search_pickup_group.set_content_layout(self.search_pickup_layout)
        self.search_pickup_model = QtGui.QStandardItemModel(0, 4, self.root)
        self.search_pickup_model.setHorizontalHeaderLabels(["World", "Region", "Area", "Location"])
        self.search_pickup_proxy = QtCore.QSortFilterProxyModel(self.root)
        self.search_pickup_proxy.setSourceModel(self.search_pickup_model)
        self.search_pickup_proxy.setFilterKeyColumn(0)
        self.search_pickup_proxy.setFilterRole(QtCore.Qt.ItemDataRole.UserRole)
        self.search_pickup_view.setModel(self.search_pickup_proxy)

        self.pickup_spoiler_pickup_combobox.currentTextChanged.connect(self._on_change_pickup_filter)
        self.pickup_spoiler_show_all_button.clicked.connect(self._toggle_show_all_pickup_spoiler)
        signal_handling.on_combo(self.search_pickup_combo, self._show_location_for_pickup)

    def widget(self) -> QtWidgets.QWidget:
        return self.root

    def tab_title(self) -> str:
        return "Pickups"

    def update_content(
        self, configuration: BaseConfiguration, all_patches: dict[int, GamePatches], players: PlayersConfiguration
    ):
        self._update_search_pickup_group(all_patches, players)

        patches = all_patches[players.player_index]
        pickup_names = {pickup.pickup.name for pickup in patches.pickup_assignment.values()}
        game_description = filtered_database.game_description_for_layout(configuration)
        self._create_pickup_spoilers(game_description)
        starting_area = game_description.region_list.area_by_area_location(patches.starting_location)

        extra_items = item_names.additional_starting_equipment(configuration, game_description, patches)

        self.spoiler_starting_location_label.setText(
            f"Starting Location: {game_description.region_list.area_name(starting_area)}"
        )
        self.spoiler_starting_items_label.setText(
            "Random Starting Items: {}".format(", ".join(extra_items) if extra_items else "None")
        )
        self._update_show_all_button_state()

        self.pickup_spoiler_pickup_combobox.clear()
        self.pickup_spoiler_pickup_combobox.addItem("None")
        for pickup_name in sorted(pickup_names):
            self.pickup_spoiler_pickup_combobox.addItem(pickup_name)

        for pickup_button in self.pickup_spoiler_buttons:
            pickup_target = patches.pickup_assignment.get(pickup_button.pickup_index)

            pickup_button.target_player = None
            if pickup_target is not None:
                pickup_button.item_name = pickup_target.pickup.name
                if players.is_multiworld:
                    pickup_button.target_player = pickup_target.player
                    pickup_button.player_names = players.player_names
            else:
                pickup_button.item_name = "Nothing"

            if not pickup_button.item_is_hidden:
                pickup_button.setText(pickup_button.item_name)

    def _create_pickup_spoilers(self, game_description: GameDescription):
        for groups in self._pickup_spoiler_region_to_group.values():
            groups.deleteLater()

        self.pickup_spoiler_show_all_button.currently_show_all = True
        self.pickup_spoiler_buttons.clear()

        self._pickup_spoiler_region_to_group = {}
        nodes_in_region = collections.defaultdict(list)

        for region, area, node in game_description.region_list.all_regions_areas_nodes:
            if isinstance(node, PickupNode):
                region_name = region.correct_name(area.in_dark_aether)
                nodes_in_region[region_name].append((f"{area.name} - {node.name}", node.pickup_index))
                continue

        for region_name in sorted(nodes_in_region.keys()):
            group_box = QtWidgets.QGroupBox(self.pickup_spoiler_scroll_contents)
            group_box.setTitle(region_name)
            vertical_layout = QtWidgets.QVBoxLayout(group_box)
            vertical_layout.setContentsMargins(8, 4, 8, 4)
            vertical_layout.setSpacing(2)
            group_box.vertical_layout = vertical_layout

            vertical_layout.horizontal_layouts = []
            self._pickup_spoiler_region_to_group[region_name] = group_box
            self.pickup_spoiler_scroll_content_layout.addWidget(group_box)

            for area_name, pickup_index in sorted(nodes_in_region[region_name], key=lambda it: it[0]):
                horizontal_layout = QtWidgets.QHBoxLayout()
                horizontal_layout.setSpacing(2)

                label = QtWidgets.QLabel(group_box)
                label.setText(area_name)
                horizontal_layout.addWidget(label)
                horizontal_layout.label = label

                push_button = QtWidgets.QPushButton(group_box)
                push_button.setFlat(True)
                push_button.setText("Hidden")
                push_button.item_is_hidden = True
                push_button.pickup_index = pickup_index
                push_button.clicked.connect(functools.partial(self._toggle_pickup_spoiler, push_button))
                push_button.item_name = "Nothing was Set, ohno"
                push_button.row = horizontal_layout
                horizontal_layout.addWidget(push_button)
                horizontal_layout.button = push_button
                self.pickup_spoiler_buttons.append(push_button)

                group_box.vertical_layout.addLayout(horizontal_layout)
                group_box.vertical_layout.horizontal_layouts.append(horizontal_layout)

    def _update_show_all_button_state(self):
        self.pickup_spoiler_show_all_button.currently_show_all = all(
            button.item_is_hidden for button in self.pickup_spoiler_buttons
        )
        if self.pickup_spoiler_show_all_button.currently_show_all:
            self.pickup_spoiler_show_all_button.setText(QtCore.QCoreApplication.translate("HistoryWindow", "Show All"))
        else:
            self.pickup_spoiler_show_all_button.setText(QtCore.QCoreApplication.translate("HistoryWindow", "Hide All"))

    def _toggle_pickup_spoiler(self, button):
        if button.item_is_hidden:
            _show_pickup_spoiler(button)
        else:
            _hide_pickup_spoiler(button)
        self._update_show_all_button_state()

    def _toggle_show_all_pickup_spoiler(self):
        if self.pickup_spoiler_show_all_button.currently_show_all:
            action = _show_pickup_spoiler
        else:
            action = _hide_pickup_spoiler

        for button in self.pickup_spoiler_buttons:
            action(button)

        self._update_show_all_button_state()

    def _on_change_pickup_filter(self, text):
        for button in self.pickup_spoiler_buttons:
            visible = text == "None" or text == button.item_name
            button.setVisible(visible)
            button.row.label.setVisible(visible)

    def _update_search_pickup_group(self, all_patches: dict[int, GamePatches], players: PlayersConfiguration):
        self.search_pickup_group.setVisible(players.is_multiworld)
        if not players.is_multiworld:
            return

        pickup_names = set()
        rows = []

        for source_index, patches in all_patches.items():
            rl = patches.game.region_list
            for pickup_index, pickup_target in patches.pickup_assignment.items():
                if pickup_target.player == players.player_index:
                    node = rl.node_from_pickup_index(pickup_index)
                    area = rl.nodes_to_area(node)

                    rows.append(
                        (
                            pickup_target.pickup.name,
                            players.player_names[source_index],
                            rl.region_name_from_area(area, True),
                            area.name,
                            node.name,
                        )
                    )
                    pickup_names.add(pickup_target.pickup.name)

        self.search_pickup_model.setRowCount(len(rows))

        for i, (pickup_name, player_name, region_name, area_name, node_name) in enumerate(rows):
            player_item = QtGui.QStandardItem(player_name)
            player_item.setData(pickup_name, QtCore.Qt.ItemDataRole.UserRole)
            self.search_pickup_model.setItem(i, 0, player_item)
            self.search_pickup_model.setItem(i, 1, QtGui.QStandardItem(region_name))
            self.search_pickup_model.setItem(i, 2, QtGui.QStandardItem(area_name))
            self.search_pickup_model.setItem(i, 3, QtGui.QStandardItem(node_name))

        self.search_pickup_combo.clear()
        self.search_pickup_combo.addItem("Select pickup", None)
        for pickup_name in sorted(pickup_names):
            self.search_pickup_combo.addItem(pickup_name, pickup_name)

    def _show_location_for_pickup(self, target: str | None):
        if target is None:
            self.search_pickup_proxy.setFilterFixedString("<@NOT PRESENT@>")
        else:
            self.search_pickup_proxy.setFilterRegularExpression(f"^{target}$")
