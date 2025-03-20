from __future__ import annotations

import typing

from randovania.game_description.game_database_view import GameDatabaseView, GameDatabaseViewProxy

if typing.TYPE_CHECKING:
    from collections.abc import Iterable

    from randovania.game_description.db.area import Area
    from randovania.game_description.db.node import Node
    from randovania.game_description.db.region import Region
    from randovania.layout.base.base_configuration import BaseConfiguration


class LayerFilteredGameDatabaseView(GameDatabaseViewProxy):
    def __init__(self, original: GameDatabaseView, enabled_layers: set[str]):
        super().__init__(original)
        self.enabled_layers = enabled_layers

    @typing.override
    def node_iterator(self) -> Iterable[tuple[Region, Area, Node]]:
        for entry in super().node_iterator():
            if self.enabled_layers.intersection(entry[2].layers):
                yield entry


def filter_view_for_configuration(view: GameDatabaseView, configuration: BaseConfiguration) -> GameDatabaseView:
    """
    Creates a new GameDatabaseView that filters what nodes are visible based on what layers are
    active in the given Configuration.
    :param view: A view to wrap
    :param configuration: The configuration to query for active layers.
    :return: A new view with filters applied
    """
    return LayerFilteredGameDatabaseView(
        view,
        configuration.active_layers(),
    )
