from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from randovania.game_description.db.area import Area
    from randovania.game_description.db.node import Node
    from randovania.game_description.db.region import Region
    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo


class GameDatabaseView:
    """
    Provides access to the GameDescription and nested, with support for being filtered for Preset settings.
    """

    def node_iterator(self) -> Iterable[tuple[Region, Area, Node]]:
        """
        Iterates over all nodes in the database, including the region and area they belong to
        """
        raise NotImplementedError

    def interesting_resources_for_damage(
        self, resource: SimpleResourceInfo, collection: ResourceCollection
    ) -> Iterator[ResourceInfo]:
        """
        Provides all interesting resources for the given damage resource
        """
        raise NotImplementedError
