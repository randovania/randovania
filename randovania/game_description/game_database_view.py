from __future__ import annotations

import typing
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from randovania.game_description.db.area import Area
    from randovania.game_description.db.dock import DockType, DockWeakness
    from randovania.game_description.db.node import Node
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.db.region import Region
    from randovania.game_description.resources.pickup_index import PickupIndex
    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo

    NodeT = typing.TypeVar("NodeT", bound=Node)


class GameDatabaseView:
    """
    Provides access to the GameDescription and nested, with support for being filtered for Preset settings.

    These APIs are all expected to be slow and shouldn't be used in any performance sensitive code.
    """

    def node_iterator(self) -> Iterable[tuple[Region, Area, Node]]:
        """
        Iterates over all nodes in the database, including the region and area they belong to
        """
        raise NotImplementedError

    def node_by_identifier(self, identifier: NodeIdentifier) -> Node:
        """
        Find a node with the given NodeIdentifier.
        Raises KeyError if no node could be found.
        """
        raise NotImplementedError

    def interesting_resources_for_damage(
        self, resource: SimpleResourceInfo, collection: ResourceCollection
    ) -> Iterator[ResourceInfo]:
        """
        Provides all interesting resources for the given damage resource
        """
        raise NotImplementedError

    def assert_pickup_index_exists(self, index: PickupIndex) -> None:
        """
        If the PickupIndex does not exist, this function raises an Exception
        """
        raise NotImplementedError

    def create_resource_collection(self) -> ResourceCollection:
        """
        Creates a new ResourceCollection
        """
        raise NotImplementedError
        # ResourceCollection

    def default_starting_location(self) -> NodeIdentifier:
        """
        The default starting location for the game. Not really used since the preset starting location replaces this...
        """
        raise NotImplementedError

    def get_dock_types(self) -> list[DockType]:
        """
        List all available DockTypes
        """
        raise NotImplementedError

    def get_dock_weakness(self, dock_type_name: str, weakness_name: str) -> DockWeakness:
        """
        Gets a DockWeakness via names
        """
        raise NotImplementedError


def typed_node_by_identifier(game: GameDatabaseView, i: NodeIdentifier, t: type[NodeT]) -> NodeT:
    """
    Wrapper for calling game.node_by_identifier, followed by an isinstance.
    """
    result = game.node_by_identifier(i)
    assert isinstance(result, t)
    return result
