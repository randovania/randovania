import dataclasses
from enum import Enum
from typing import Optional, NamedTuple, Tuple

from randovania.game_description.world.area_location import AreaLocation
from randovania.game_description.world.dock import DockWeakness, DockConnection
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.requirements import ResourceRequirement, Requirement, RequirementAnd
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.logbook_asset import LogbookAsset
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceInfo, ResourceGain, CurrentResources
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.resources.translator_gate import TranslatorGate
from randovania.game_description.world.teleporter import Teleporter


class NodeLocation(NamedTuple):
    x: float
    y: float
    z: float


@dataclasses.dataclass(frozen=True)
class Node:
    name: str
    heal: bool
    location: Optional[NodeLocation]
    index: int

    def __lt__(self, other):
        return self.name < other.name

    def __hash__(self):
        return hash((self.index, self.name))

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

    def can_collect(self, patches: GamePatches, current_resources: CurrentResources,
                    all_nodes: Tuple[Node, ...], database: ResourceDatabase) -> bool:
        raise NotImplementedError

    def resource_gain_on_collect(self, patches: GamePatches, current_resources: CurrentResources,
                                 all_nodes: Tuple[Node, ...], database: ResourceDatabase) -> ResourceGain:
        raise NotImplementedError


@dataclasses.dataclass(frozen=True)
class GenericNode(Node):
    pass


@dataclasses.dataclass(frozen=True)
class DockNode(Node):
    dock_index: int
    default_connection: DockConnection
    default_dock_weakness: DockWeakness

    def __hash__(self):
        return hash((self.index, self.name, self.dock_index))

    def __repr__(self):
        return "DockNode({!r}/{} -> {})".format(self.name, self.dock_index, self.default_connection)


@dataclasses.dataclass(frozen=True)
class TeleporterNode(Node):
    teleporter: Optional[Teleporter]
    default_connection: AreaLocation
    scan_asset_id: Optional[int]
    keep_name_when_vanilla: bool
    editable: bool

    @property
    def teleporter_instance_id(self) -> Optional[int]:
        if self.teleporter is not None:
            return self.teleporter.instance_id

    def __post_init__(self):
        if self.editable and self.teleporter is None:
            raise ValueError(f"{self!r} is editable, but teleporter is None")

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

    def can_collect(self, patches: GamePatches, current_resources: CurrentResources,
                    all_nodes: Tuple[Node, ...], database: ResourceDatabase) -> bool:
        return current_resources.get(self.pickup_index, 0) == 0

    def resource_gain_on_collect(self, patches: GamePatches, current_resources: CurrentResources,
                                 all_nodes: Tuple[Node, ...], database: ResourceDatabase) -> ResourceGain:
        yield self.pickup_index, 1

        target = patches.pickup_assignment.get(self.pickup_index)
        if target is not None and target.player == patches.player_index:
            yield from target.pickup.resource_gain(current_resources, force_lock=True)


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

    def can_collect(self, patches: GamePatches, current_resources: CurrentResources,
                    all_nodes: Tuple[Node, ...], database: ResourceDatabase) -> bool:
        return current_resources.get(self.event, 0) == 0

    def resource_gain_on_collect(self, patches: GamePatches, current_resources,
                                 all_nodes: Tuple[Node, ...], database: ResourceDatabase) -> ResourceGain:
        yield self.event, 1


@dataclasses.dataclass(frozen=True)
class TranslatorGateNode(ResourceNode):
    gate: TranslatorGate
    scan_visor: ItemResourceInfo

    def __repr__(self):
        return "TranslatorGateNode({!r} -> {})".format(self.name, self.gate.index)

    def requirement_to_leave(self, patches: GamePatches, current_resources: CurrentResources) -> Requirement:
        return RequirementAnd([
            ResourceRequirement(patches.translator_gates[self.gate], 1, False),
            ResourceRequirement(self.scan_visor, 1, False),
        ])

    def resource(self) -> ResourceInfo:
        return self.gate

    def can_collect(self, patches: GamePatches, current_resources: CurrentResources,
                    all_nodes: Tuple[Node, ...], database: ResourceDatabase) -> bool:
        """
        Checks if this TranslatorGate can be opened with the given resources and translator gate mapping
        :param patches:
        :param current_resources:
        :param all_nodes:
        :param database:
        :return:
        """
        if current_resources.get(self.gate, 0) != 0:
            return False
        translator = patches.translator_gates[self.gate]
        return current_resources.get(self.scan_visor, 0) > 0 and current_resources.get(translator, 0) > 0

    def resource_gain_on_collect(self, patches: GamePatches, current_resources: CurrentResources,
                                 all_nodes: Tuple[Node, ...], database: ResourceDatabase) -> ResourceGain:
        yield self.gate, 1


class LoreType(Enum):
    LUMINOTH_LORE = "luminoth-lore"
    LUMINOTH_WARRIOR = "luminoth-warrior"
    PIRATE_LORE = "pirate-lore"
    SKY_TEMPLE_KEY_HINT = "sky-temple-key-hint"

    @property
    def holds_generic_hint(self) -> bool:
        return self in {LoreType.LUMINOTH_LORE, LoreType.PIRATE_LORE}

    @property
    def long_name(self) -> str:
        return _LORE_TYPE_LONG_NAME[self]


_LORE_TYPE_LONG_NAME = {
    LoreType.LUMINOTH_LORE: "Luminoth Lore",
    LoreType.LUMINOTH_WARRIOR: "Keybearer Corpse",
    LoreType.PIRATE_LORE: "Pirate Lore",
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
        items = [ResourceRequirement(self.scan_visor, 1, False)]
        if self.required_translator is not None:
            items.append(ResourceRequirement(self.required_translator, 1, False))

        return RequirementAnd(items)

    def resource(self) -> ResourceInfo:
        return LogbookAsset(self.string_asset_id)

    def can_collect(self, patches: GamePatches, current_resources: CurrentResources,
                    all_nodes: Tuple[Node, ...], database: ResourceDatabase) -> bool:
        """
        Checks if this TranslatorGate can be opened with the given resources and translator gate mapping
        :param patches:
        :param current_resources:
        :param all_nodes:
        :param database:
        :return:
        """
        if current_resources.get(self.resource(), 0) != 0:
            return False

        if current_resources.get(self.scan_visor, 0) == 0:
            return False

        if self.required_translator is not None:
            return current_resources.get(self.required_translator, 0) > 0
        else:
            return True

    def resource_gain_on_collect(self, patches: GamePatches, current_resources: CurrentResources,
                                 all_nodes: Tuple[Node, ...], database: ResourceDatabase) -> ResourceGain:
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
        return SimpleResourceInfo(self.index, f"Ship Node {self.index}", f"Ship{self.index}", ResourceType.SHIP_NODE)

    def can_collect(self, patches: GamePatches, current_resources: CurrentResources,
                    all_nodes: Tuple[Node, ...], database: ResourceDatabase) -> bool:
        """
        Checks if this TranslatorGate can be opened with the given resources and translator gate mapping
        :param patches:
        :param current_resources:
        :param all_nodes:
        :param database:
        :return:
        """
        if current_resources.get(self.item_to_summon, 0) == 0 and current_resources.get(self.resource(), 0) == 0:
            return False

        return any(
            current_resources.get(node.resource(), 0) == 0
            for node in all_nodes
            if isinstance(node, PlayerShipNode) and node.is_unlocked.satisfied(current_resources, 0, database)
        )

    def resource_gain_on_collect(self, patches: GamePatches, current_resources: CurrentResources,
                                 all_nodes: Tuple[Node, ...], database: ResourceDatabase) -> ResourceGain:
        for node in all_nodes:
            if isinstance(node, PlayerShipNode) and node.is_unlocked.satisfied(current_resources, 0, database):
                yield node.resource(), 1
