from __future__ import annotations

import dataclasses
import typing
from enum import Enum
from typing import Optional, NamedTuple, Tuple, Dict

from frozendict import frozendict

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.requirements import ResourceRequirement, Requirement, RequirementAnd
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.logbook_asset import LogbookAsset
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceInfo, ResourceGain, CurrentResources
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.dock import DockWeakness, DockType
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.lib import frozen_lib


class NodeLocation(NamedTuple):
    x: float
    y: float
    z: float


class NodeContext(NamedTuple):
    self_identifier: NodeIdentifier
    patches: GamePatches
    current_resources: CurrentResources
    all_nodes: Tuple[Node, ...]
    database: ResourceDatabase


@dataclasses.dataclass(frozen=True)
class Node:
    name: str
    heal: bool
    location: Optional[NodeLocation]
    description: str
    extra: Dict[str, typing.Any]
    index: int

    def __lt__(self, other):
        return self.name < other.name

    def __hash__(self):
        return hash((self.index, self.name))

    def __post_init__(self):
        if not isinstance(self.extra, frozendict):
            if not isinstance(self.extra, dict):
                raise ValueError(f"Expected dict for extra, got {type(self.extra)}")
            object.__setattr__(self, "extra", frozen_lib.wrap(self.extra))

    @property
    def is_resource_node(self) -> bool:
        return False

    def requirement_to_leave(self, patches: GamePatches, current_resources: CurrentResources) -> Requirement:
        return Requirement.trivial()


@dataclasses.dataclass(frozen=True)
class ResourceNode(Node):
    @property
    def is_resource_node(self) -> bool:
        return True

    def resource(self) -> ResourceInfo:
        raise NotImplementedError

    def can_collect(self, context: NodeContext) -> bool:
        raise NotImplementedError

    def resource_gain_on_collect(self, context: NodeContext) -> ResourceGain:
        raise NotImplementedError


@dataclasses.dataclass(frozen=True)
class GenericNode(Node):
    pass


@dataclasses.dataclass(frozen=True)
class DockNode(Node):
    """
    Represents a connection to another area via something similar to a door and it's always to another DockNode.
    The dock weakness describes the types of door the game might have, which could be randomized separately from where
    the door leads to.

    This is the default way a node connects to another area, expected to be used in every area and it implies the
    areas are "physically" next to each other.

    TeleporterNode is expected to be used exceptionally, where it can be reasonable to list all of them in the
    UI for user selection (elevator rando, for example).
    """
    default_connection: NodeIdentifier
    dock_type: DockType
    default_dock_weakness: DockWeakness

    def __hash__(self):
        return hash((self.index, self.name, self.default_connection))

    def __repr__(self):
        return "DockNode({!r} -> {})".format(self.name, self.default_connection)


@dataclasses.dataclass(frozen=True)
class TeleporterNode(Node):
    default_connection: AreaIdentifier
    keep_name_when_vanilla: bool
    editable: bool

    def __repr__(self):
        return "TeleporterNode({!r} -> {})".format(self.name, self.default_connection)


@dataclasses.dataclass(frozen=True)
class PickupNode(ResourceNode):
    pickup_index: PickupIndex
    major_location: bool

    def __repr__(self):
        return "PickupNode({!r} -> {})".format(self.name, self.pickup_index.index)

    def requirement_to_leave(self, patches: GamePatches, current_resources: CurrentResources) -> Requirement:
        # FIXME: using non-resource as key in CurrentResources
        if current_resources.get("add_self_as_requirement_to_resources") == 1:
            return ResourceRequirement(self.pickup_index, 1, False)
        else:
            return Requirement.trivial()

    def resource(self) -> ResourceInfo:
        return self.pickup_index

    def can_collect(self, context: NodeContext) -> bool:
        return context.current_resources.get(self.pickup_index, 0) == 0

    def resource_gain_on_collect(self, context: NodeContext) -> ResourceGain:
        yield self.pickup_index, 1

        patches = context.patches
        target = patches.pickup_assignment.get(self.pickup_index)
        if target is not None and target.player == patches.player_index:
            yield from target.pickup.resource_gain(context.current_resources, force_lock=True)


@dataclasses.dataclass(frozen=True)
class EventNode(ResourceNode):
    event: ResourceInfo

    def __repr__(self):
        return "EventNode({!r} -> {})".format(self.name, self.event.long_name)

    def requirement_to_leave(self, patches: GamePatches, current_resources: CurrentResources) -> Requirement:
        if current_resources.get("add_self_as_requirement_to_resources") == 1:
            return ResourceRequirement(self.event, 1, False)
        else:
            return Requirement.trivial()

    def resource(self) -> ResourceInfo:
        return self.event

    def can_collect(self, context: NodeContext) -> bool:
        return context.current_resources.get(self.event, 0) == 0

    def resource_gain_on_collect(self, context: NodeContext) -> ResourceGain:
        yield self.event, 1


@dataclasses.dataclass(frozen=True)
class ConfigurableNode(Node):
    self_identifier: NodeIdentifier

    def __repr__(self):
        return "ConfigurableNode({!r})".format(self.name)

    def requirement_to_leave(self, patches: GamePatches, current_resources: CurrentResources) -> Requirement:
        return patches.configurable_nodes[self.self_identifier]


class LoreType(Enum):
    REQUIRES_ITEM = "requires-item"
    SPECIFIC_PICKUP = "specific-pickup"
    GENERIC = "generic"
    SKY_TEMPLE_KEY_HINT = "sky-temple-key-hint"

    @property
    def holds_generic_hint(self) -> bool:
        return self in {LoreType.REQUIRES_ITEM, LoreType.GENERIC}

    @property
    def long_name(self) -> str:
        return _LORE_TYPE_LONG_NAME[self]


_LORE_TYPE_LONG_NAME = {
    LoreType.REQUIRES_ITEM: "Requires Item",
    LoreType.SPECIFIC_PICKUP: "Specific Pickup",
    LoreType.GENERIC: "Generic",
    LoreType.SKY_TEMPLE_KEY_HINT: "Sky Temple Key Hint",
}


@dataclasses.dataclass(frozen=True)
class LogbookNode(ResourceNode):
    string_asset_id: int
    scan_visor: ItemResourceInfo
    lore_type: LoreType
    required_translator: Optional[ItemResourceInfo]
    hint_index: Optional[int]

    def __repr__(self):
        extra = None
        if self.required_translator is not None:
            extra = self.required_translator.short_name
        elif self.hint_index is not None:
            extra = self.hint_index
        return "LogbookNode({!r} -> {}/{}{})".format(
            self.name,
            self.string_asset_id,
            self.lore_type.value,
            f"/{extra}" if extra is not None else ""
        )

    def requirement_to_leave(self, patches: GamePatches, current_resources: CurrentResources) -> Requirement:
        items = []
        if self.scan_visor is not None:
            items.append(ResourceRequirement(self.scan_visor, 1, False))
        if self.required_translator is not None:
            items.append(ResourceRequirement(self.required_translator, 1, False))

        return RequirementAnd(items)

    def resource(self) -> ResourceInfo:
        return LogbookAsset(self.string_asset_id)

    def can_collect(self, context: NodeContext) -> bool:
        """
        Checks if this TranslatorGate can be opened with the given resources and translator gate mapping
        :param context:
        :return:
        """
        current_resources = context.current_resources
        if current_resources.get(self.resource(), 0) != 0:
            return False

        if self.scan_visor is not None:
            if current_resources.get(self.scan_visor, 0) == 0:
                return False

        if self.required_translator is not None:
            return current_resources.get(self.required_translator, 0) > 0

        return True

    def resource_gain_on_collect(self, context: NodeContext) -> ResourceGain:
        yield self.resource(), 1


@dataclasses.dataclass(frozen=True)
class PlayerShipNode(ResourceNode):
    is_unlocked: Requirement
    item_to_summon: ItemResourceInfo

    @property
    def visor_requirement(self):
        return ResourceRequirement(self.item_to_summon, 1, False)

    def requirement_to_leave(self, patches: GamePatches, current_resources: CurrentResources) -> Requirement:
        return RequirementAnd([self.is_unlocked, ResourceRequirement(self.resource(), 1, False)])

    def resource(self) -> SimpleResourceInfo:
        return SimpleResourceInfo(f"Ship Node {self.index}", f"Ship{self.index}", ResourceType.SHIP_NODE)

    def can_collect(self, context: NodeContext) -> bool:
        """
        Checks if this TranslatorGate can be opened with the given resources and translator gate mapping
        :param context:
        :return:
        """
        current_resources = context.current_resources
        if current_resources.get(self.item_to_summon, 0) == 0 and current_resources.get(self.resource(), 0) == 0:
            return False

        return any(
            current_resources.get(node.resource(), 0) == 0
            for node in context.all_nodes
            if isinstance(node, PlayerShipNode) and node.is_unlocked.satisfied(current_resources, 0, context.database)
        )

    def resource_gain_on_collect(self, context: NodeContext) -> ResourceGain:
        for node in context.all_nodes:
            if isinstance(node, PlayerShipNode) and node.is_unlocked.satisfied(
                    context.current_resources, 0, context.database):
                yield node.resource(), 1
