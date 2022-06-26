import collections
import functools

from PySide6 import QtWidgets, QtCore

from randovania.exporter import item_names
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.world.pickup_node import PickupNode
from randovania.games.game import RandovaniaGame
from randovania.gui.game_details.game_details_tab import GameDetailsTab
from randovania.gui.generated.pickup_details_tab_ui import Ui_PickupDetailsTab
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout import filtered_database
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
        self._pickup_spoiler_world_to_group = {}

        self.pickup_spoiler_pickup_combobox.currentTextChanged.connect(self._on_change_pickup_filter)
        self.pickup_spoiler_show_all_button.clicked.connect(self._toggle_show_all_pickup_spoiler)

    def widget(self) -> QtWidgets.QWidget:
        return self.root

    def tab_title(self) -> str:
        return "Pickups"

    def update_content(self, configuration: BaseConfiguration, all_patches: dict[int, GamePatches],
                       players: PlayersConfiguration):
        patches = all_patches[players.player_index]
        pickup_names = {
            pickup.pickup.name
            for pickup in patches.pickup_assignment.values()
        }
        game_description = filtered_database.game_description_for_layout(configuration)
        self._create_pickup_spoilers(game_description)
        starting_area = game_description.world_list.area_by_area_location(patches.starting_location)

        extra_items = item_names.additional_starting_items(configuration,
                                                           game_description.resource_database,
                                                           patches.starting_items)

        self.spoiler_starting_location_label.setText("Starting Location: {}".format(
            game_description.world_list.area_name(starting_area)
        ))
        self.spoiler_starting_items_label.setText("Random Starting Items: {}".format(
            ", ".join(extra_items)
            if extra_items else "None"
        ))
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
        for groups in self._pickup_spoiler_world_to_group.values():
            groups.deleteLater()

        self.pickup_spoiler_show_all_button.currently_show_all = True
        self.pickup_spoiler_buttons.clear()

        self._pickup_spoiler_world_to_group = {}
        nodes_in_world = collections.defaultdict(list)

        for world, area, node in game_description.world_list.all_worlds_areas_nodes:
            if isinstance(node, PickupNode):
                world_name = world.correct_name(area.in_dark_aether)
                nodes_in_world[world_name].append((f"{area.name} - {node.name}", node.pickup_index))
                continue

        for world_name in sorted(nodes_in_world.keys()):
            group_box = QtWidgets.QGroupBox(self.pickup_spoiler_scroll_contents)
            group_box.setTitle(world_name)
            vertical_layout = QtWidgets.QVBoxLayout(group_box)
            vertical_layout.setContentsMargins(8, 4, 8, 4)
            vertical_layout.setSpacing(2)
            group_box.vertical_layout = vertical_layout

            vertical_layout.horizontal_layouts = []
            self._pickup_spoiler_world_to_group[world_name] = group_box
            self.pickup_spoiler_scroll_content_layout.addWidget(group_box)

            for area_name, pickup_index in sorted(nodes_in_world[world_name], key=lambda it: it[0]):
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
