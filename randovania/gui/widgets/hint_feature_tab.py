from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QLabel, QSizePolicy, QSpacerItem, QVBoxLayout, QWidget

from randovania.game_description.db.pickup_node import PickupNode
from randovania.gui.generated.hint_feature_tab_ui import Ui_HintFeatureTab
from randovania.gui.lib.data_editor_links import (
    data_editor_href,
    on_click_data_editor_link,
)
from randovania.gui.lib.foldable import Foldable

if TYPE_CHECKING:
    from collections.abc import Iterable

    from randovania.game_description.db.area_identifier import AreaIdentifier
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.hint_features import HintFeature
    from randovania.game_description.pickup.pickup_database import PickupDatabase
    from randovania.game_description.pickup.pickup_definition.base_pickup import BasePickupDefinition
    from randovania.gui.lib.window_manager import WindowManager


class HintFeatureTab(QWidget, Ui_HintFeatureTab):
    """Base class for GUI tabs listing HintFeatures"""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setupUi(self)
        self.description_label.setText(self.description)
        self.feature_widgets: dict[HintFeature, Foldable] = {}

    @property
    def element_type(self) -> str:
        """A short name for the type of element with the feature"""

        raise NotImplementedError

    @property
    def description(self) -> str:
        """The description displayed at the top of the tab"""

        return (
            f"When a {self.element_type} is referenced in a hint, "
            f"the hint may refer to it using a Feature of varying precision. "
            f"The following is a list of which {self.element_type}s a given Feature may refer to."
        )

    def add_feature_widget(self, feature: HintFeature, elements_with_feature: list[str]) -> None:
        """Adds a Foldable list of elements with a given feature to the tab"""

        if not elements_with_feature:
            return

        title = f'{feature.long_name}: "{feature.hint_details[0]}{feature.hint_details[1]}"'

        feature_widget = Foldable(self, title)
        self.feature_widgets[feature] = feature_widget

        feature_widget.setObjectName(f"feature_box {feature.name}")
        feature_layout = QVBoxLayout()
        feature_layout.setObjectName(f"feature_layout {feature.name}")
        feature_widget.set_content_layout(feature_layout)

        if feature.description:
            feature_description_label = QLabel(feature.description, feature_widget)
            feature_layout.addWidget(feature_description_label)

        for i, element in enumerate(elements_with_feature):
            element_label = self.create_element_label(feature, element)
            element_label.setObjectName(f"feature_label {feature.name} {i}")
            feature_layout.addWidget(element_label)

        self.scroll_area_contents.layout().addWidget(feature_widget)

    def create_element_label(self, feature: HintFeature, element: str) -> QLabel:
        """Creates a label to refer to the given element."""
        return QLabel(element, self.feature_widgets[feature])

    def add_spacer(self) -> None:
        """Adds a vertical spacer to the tab"""

        spacer = QSpacerItem(
            20,
            40,
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Expanding,
        )
        self.scroll_area_contents.layout().addItem(spacer)


def _keyfunc(feature: HintFeature) -> str:
    return feature.hint_details.description


class LocationHintFeatureTab(HintFeatureTab):
    @property
    def element_type(self) -> str:
        return "location"

    @property
    def description(self) -> str:
        return (
            super().description
            + "\n\n"
            + (
                '**As a general rule, the wording "near" means that the '
                "pickup location is in the same room as the feature.**"
            )
        )

    def create_element_label(self, feature: HintFeature, element: str):
        element_label = super().create_element_label(feature, element)
        element_label.linkActivated.connect(
            on_click_data_editor_link(
                self._window_manager,
                self._game.game,
            )
        )
        return element_label

    def add_features(self, game: GameDescription, window_manager: WindowManager) -> None:
        self._game = game
        self._window_manager = window_manager

        for feature in sorted(game.hint_feature_database.values(), key=_keyfunc):
            if feature.hidden:
                continue

            # sort normally, but put dark regions immediately after their light region
            def nodes_keyfunc(node: PickupNode) -> tuple[str, bool, str, str]:
                id_ = node.identifier
                area = game.region_list.area_by_area_location(id_.area_identifier)

                return id_.region, area.in_dark_aether, id_.area, id_.node

            sorted_nodes = sorted(
                game.region_list.pickup_nodes_with_feature(feature),
                key=nodes_keyfunc,
            )

            # group pickup nodes by area
            feature_nodes: dict[AreaIdentifier, list[PickupNode]] = defaultdict(list)
            for node in sorted_nodes:
                feature_nodes[node.identifier.area_identifier].append(node)

            node_links: list[str] = []

            for area_id, nodes in feature_nodes.items():
                region, area = game.region_list.region_and_area_by_area_identifier(area_id)
                url = data_editor_href(region, area)

                if len(nodes) == len([node for node in area.actual_nodes if isinstance(node, PickupNode)]):
                    node_links.append(url)
                    continue

                for node in nodes:
                    node_links.append(f"{url} ({node.name})")

            self.add_feature_widget(feature, node_links)
        self.add_spacer()


class PickupHintFeatureTab(HintFeatureTab):
    @property
    def element_type(self) -> str:
        return "pickup"

    def add_features(self, pickup_db: PickupDatabase) -> None:
        for feature in sorted(pickup_db.pickup_categories.values(), key=_keyfunc):
            if feature.hidden:
                continue

            def pickups_with_feature(group: dict[str, BasePickupDefinition]) -> Iterable[str]:
                yield from (name for name, pickup in group.items() if feature in pickup.hint_features)

            pickup_names: list[str] = []
            pickup_names.extend(pickups_with_feature(pickup_db.generated_pickups))
            pickup_names.extend(pickups_with_feature(pickup_db.standard_pickups))
            pickup_names.extend(pickups_with_feature(pickup_db.ammo_pickups))

            self.add_feature_widget(feature, pickup_names)
        self.add_spacer()
