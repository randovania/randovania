from __future__ import annotations

import abc
from abc import ABC
from typing import TYPE_CHECKING, final, override

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

    from randovania.game_description.db.area import Area
    from randovania.game_description.db.dock import DockType, DockWeakness
    from randovania.game_description.db.node import Node
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.db.pickup_node import PickupNode
    from randovania.game_description.db.region import Region
    from randovania.game_description.hint_features import HintFeature
    from randovania.game_description.pickup.pickup_database import PickupDatabase
    from randovania.game_description.pickup.pickup_entry import PickupModel
    from randovania.game_description.requirements.base import Requirement
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo
    from randovania.game_description.resources.pickup_index import PickupIndex
    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.game_description.resources.resource_database import NamedRequirementTemplate
    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.game_description.resources.resource_type import ResourceType
    from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
    from randovania.game_description.resources.trick_resource_info import TrickResourceInfo


class ResourceDatabaseView(ABC):
    """
    An interface for giving access to a database of resources.
    """

    @abc.abstractmethod
    def get_item(self, short_name: str) -> ItemResourceInfo:
        """
        Gets a ItemResourceInfo, using internal name
        Raises KeyError if it doesn't exist.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_event(self, short_name: str) -> SimpleResourceInfo:
        """
        Gets a ResourceInfo of type EVENT, using internal name
        Raises KeyError if it doesn't exist.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_misc(self, short_name: str) -> SimpleResourceInfo:
        """
        Gets a ResourceInfo of type MISC, using internal name
        Raises KeyError if it doesn't exist.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_trick(self, short_name: str) -> TrickResourceInfo:
        """
        Gets a TrickResourceInfo using internal name
        Raises KeyError if it doesn't exist.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_all_tricks(self) -> Sequence[TrickResourceInfo]:
        """
        Gets a list of all TrickResourceInfo
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_damage(self, short_name: str) -> SimpleResourceInfo:
        """
        Gets a ResourceInfo of type Damage, using internal name
        Raises KeyError if it doesn't exist.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_damage_reduction(self, resource: SimpleResourceInfo, current_resources: ResourceCollection) -> float:
        """
        Gets the damage reduction for given resource with the given current resources.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_template_requirement(self, name: str) -> NamedRequirementTemplate:
        """
        Gets a RequirementTemplate, using internal name.
        Raises KeyError if it doesn't exist.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_all_resources_of_type(self, resource_type: ResourceType) -> Sequence[ResourceInfo]:
        """
        Gets a list of all resources of the given type.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_pickup_model(self, name: str) -> PickupModel:
        """
        Gets a model with the given name.
        """
        raise NotImplementedError


class ResourceDatabaseViewProxy(ResourceDatabaseView):
    """
    A ResourceDatabaseView, implemented by delegating all calls to another ResourceDatabaseView.
    Intended to be used to overwrite specific functions.
    """

    def __init__(self, original: ResourceDatabaseView):
        self._original = original

    @override
    def get_item(self, short_name: str) -> ItemResourceInfo:
        return self._original.get_item(short_name)

    @override
    def get_event(self, short_name: str) -> SimpleResourceInfo:
        return self._original.get_event(short_name)

    @override
    def get_misc(self, short_name: str) -> SimpleResourceInfo:
        return self._original.get_misc(short_name)

    @override
    def get_trick(self, short_name: str) -> TrickResourceInfo:
        return self._original.get_trick(short_name)

    @override
    def get_all_tricks(self) -> Sequence[TrickResourceInfo]:
        return self._original.get_all_tricks()

    @override
    def get_damage(self, short_name: str) -> SimpleResourceInfo:
        return self._original.get_damage(short_name)

    @override
    def get_damage_reduction(self, resource: SimpleResourceInfo, current_resources: ResourceCollection) -> float:
        return self._original.get_damage_reduction(resource, current_resources)

    @override
    def get_template_requirement(self, name: str) -> NamedRequirementTemplate:
        return self._original.get_template_requirement(name)

    @override
    def get_all_resources_of_type(self, resource_type: ResourceType) -> Sequence[ResourceInfo]:
        return self._original.get_all_resources_of_type(resource_type)

    @override
    def get_pickup_model(self, name: str) -> PickupModel:
        return self._original.get_pickup_model(name)


class GameDatabaseView(ABC):
    """
    Provides access to the GameDescription and nested, with support for being filtered for Preset settings.

    These APIs are all expected to be slow and shouldn't be used in any performance sensitive code.
    """

    @abc.abstractmethod
    def node_iterator(self) -> Iterator[tuple[Region, Area, Node]]:
        """
        Iterates over all nodes in the database, including the region and area they belong to
        """

    @final
    def iterate_nodes_of_type[NodeT: Node](self, node_type: type[NodeT]) -> Iterator[tuple[Region, Area, NodeT]]:
        """
        Iterates over only the nodes that are of the given type.
        """
        yield from ((region, area, node) for region, area, node in self.node_iterator() if isinstance(node, node_type))

    @abc.abstractmethod
    def node_by_identifier(self, identifier: NodeIdentifier) -> Node:
        """
        Find a node with the given NodeIdentifier.
        Raises KeyError if no node could be found.
        """

    @final
    def typed_node_by_identifier[NodeT: Node](self, i: NodeIdentifier, t: type[NodeT]) -> NodeT:
        """
        Wrapper for calling node_by_identifier, followed by an isinstance.
        """
        result = self.node_by_identifier(i)
        if isinstance(result, t):
            return result
        raise KeyError(f"Node at {i} is an {type(result)}, not {t}")

    @abc.abstractmethod
    def assert_pickup_index_exists(self, index: PickupIndex) -> None:
        """
        If the PickupIndex does not exist, this function raises an Exception
        """

    @abc.abstractmethod
    def create_resource_collection(self) -> ResourceCollection:
        """
        Creates a new ResourceCollection
        """

    @abc.abstractmethod
    def default_starting_location(self) -> NodeIdentifier:
        """
        The default starting location for the game. Not really used since the preset starting location replaces this...
        """

    @abc.abstractmethod
    def get_dock_types(self) -> list[DockType]:
        """
        List all available DockTypes
        """

    @abc.abstractmethod
    def get_dock_weakness(self, dock_type_name: str, weakness_name: str) -> DockWeakness:
        """
        Gets a DockWeakness via names
        """

    @abc.abstractmethod
    def get_resource_database_view(self) -> ResourceDatabaseView:
        """
        Gets a view for the ResourceDatabase
        """

    @abc.abstractmethod
    def get_pickup_database(self) -> PickupDatabase:
        """
        Gets the PickupDatabase for this game.
        """

    @abc.abstractmethod
    def get_victory_condition(self) -> Requirement:
        """
        Gets the requirement that determines if the player has won.
        """

    @abc.abstractmethod
    def pickup_nodes_with_feature(self, feature: HintFeature) -> tuple[PickupNode, ...]:
        """
        Returns an iterable tuple of PickupNodes with the given feature (either directly or in their area)
        """

    @abc.abstractmethod
    def node_from_pickup_index(self, index: PickupIndex) -> PickupNode:
        """
        Returns the PickupNode with the given index.
        :raises: KeyError if it doesn't exist
        """

    @abc.abstractmethod
    def area_from_node(self, node: Node) -> Area:
        """
        Returns the Area that contains the given node.
        :raises: KeyError if it doesn't exist
        """


class GameDatabaseViewProxy(GameDatabaseView):
    """
    A GameDatabaseView, implemented by delegating all calls to another GameDatabaseView.
    Intended to be used to overwrite specific functions.
    """

    def __init__(self, original: GameDatabaseView):
        self._original = original

    @override
    def node_iterator(self) -> Iterator[tuple[Region, Area, Node]]:
        return self._original.node_iterator()

    @override
    def node_by_identifier(self, identifier: NodeIdentifier) -> Node:
        return self._original.node_by_identifier(identifier)

    @override
    def assert_pickup_index_exists(self, index: PickupIndex) -> None:
        return self._original.assert_pickup_index_exists(index)

    @override
    def create_resource_collection(self) -> ResourceCollection:
        return self._original.create_resource_collection()

    @override
    def default_starting_location(self) -> NodeIdentifier:
        return self._original.default_starting_location()

    @override
    def get_dock_types(self) -> list[DockType]:
        return self._original.get_dock_types()

    @override
    def get_dock_weakness(self, dock_type_name: str, weakness_name: str) -> DockWeakness:
        return self._original.get_dock_weakness(dock_type_name, weakness_name)

    @override
    def get_resource_database_view(self) -> ResourceDatabaseView:
        return self._original.get_resource_database_view()

    @override
    def get_pickup_database(self) -> PickupDatabase:
        return self._original.get_pickup_database()

    @override
    def get_victory_condition(self) -> Requirement:
        return self._original.get_victory_condition()

    @override
    def pickup_nodes_with_feature(self, feature: HintFeature) -> tuple[PickupNode, ...]:
        return self._original.pickup_nodes_with_feature(feature)

    @override
    def node_from_pickup_index(self, index: PickupIndex) -> PickupNode:
        return self._original.node_from_pickup_index(index)

    @override
    def area_from_node(self, node: Node) -> Area:
        return self._original.area_from_node(node)
