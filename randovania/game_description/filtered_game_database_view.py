from __future__ import annotations

import typing_extensions

from randovania.game_description.game_database_view import GameDatabaseView, GameDatabaseViewProxy

if typing_extensions.TYPE_CHECKING:
    from collections.abc import Iterable

    from randovania.game_description.db.area import Area
    from randovania.game_description.db.node import Node
    from randovania.game_description.db.region import Region


class LayerFilteredGameDatabaseView(GameDatabaseViewProxy):
    def __init__(self, original: GameDatabaseView, enabled_layers: set[str]):
        super().__init__(original)
        self.enabled_layers = enabled_layers

    @typing_extensions.override
    def node_iterator(self) -> Iterable[tuple[Region, Area, Node]]:
        for entry in super().node_iterator():
            if self.enabled_layers.intersection(entry[2].layers):
                yield entry
