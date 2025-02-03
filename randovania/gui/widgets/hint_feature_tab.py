from collections.abc import Iterable

from PySide6.QtWidgets import QLabel, QSizePolicy, QSpacerItem, QVBoxLayout, QWidget

from randovania.game_description.game_description import GameDescription
from randovania.game_description.hint_features import HintFeature
from randovania.game_description.pickup.pickup_database import PickupDatabase
from randovania.game_description.pickup.pickup_definition.base_pickup import BasePickupDefinition
from randovania.gui.generated.hint_feature_tab_ui import Ui_HintFeatureTab
from randovania.gui.lib.foldable import Foldable


class HintFeatureTab(QWidget, Ui_HintFeatureTab):
    """Base class for GUI tabs listing HintFeatures"""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setupUi(self)
        self.description_label.setText(self.description)

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
            f"The following is a list of which {self.element_type}s a given Feature may refer to:"
        )

    def add_feature_widget(self, feature: HintFeature, elements_with_feature: list[str]) -> None:
        """Adds a Foldable list of elements with a given feature to the tab"""

        if not elements_with_feature:
            return

        title = f'{feature.long_name}: "{feature.hint_details[0]}{feature.hint_details[1]}"'

        feature_widget = Foldable(self, title)
        feature_widget.setObjectName(f"feature_box {feature.name}")
        feature_layout = QVBoxLayout()
        feature_layout.setObjectName(f"feature_layout {feature.name}")
        feature_widget.set_content_layout(feature_layout)

        for i, element in enumerate(elements_with_feature):
            element_label = QLabel(element, feature_widget)
            element_label.setObjectName(f"feature_label {feature.name} {i}")
            feature_layout.addWidget(element_label)

        self.scroll_area_contents.layout().addWidget(feature_widget)

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

    def add_features(self, game: GameDescription) -> None:
        for feature in sorted(game.hint_feature_database.values(), key=_keyfunc):
            if feature.long_name.startswith("_"):
                continue

            node_names = [node.identifier.as_string for node in game.region_list.pickup_nodes_with_feature(feature)]
            self.add_feature_widget(feature, node_names)
        self.add_spacer()


class PickupHintFeatureTab(HintFeatureTab):
    @property
    def element_type(self) -> str:
        return "pickup"

    def add_features(self, pickup_db: PickupDatabase) -> None:
        for feature in sorted(pickup_db.pickup_categories.values(), key=_keyfunc):
            if feature.long_name.startswith("_"):
                continue

            def pickups_with_feature(group: dict[str, BasePickupDefinition]) -> Iterable[str]:
                yield from (name for name, pickup in group.items() if feature in pickup.hint_features)

            pickup_names: list[str] = []
            pickup_names.extend(pickups_with_feature(pickup_db.generated_pickups))
            pickup_names.extend(pickups_with_feature(pickup_db.standard_pickups))
            pickup_names.extend(pickups_with_feature(pickup_db.ammo_pickups))

            self.add_feature_widget(feature, pickup_names)
        self.add_spacer()
