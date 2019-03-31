import dataclasses

from randovania.game_description.area_location import AreaLocation
from randovania.game_description.dock import DockWeakness, DockConnection
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.requirements import RequirementSet, RequirementList, IndividualRequirement
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_info import ResourceInfo, ResourceGain, CurrentResources
from randovania.game_description.resources.translator_gate import TranslatorGate


@dataclasses.dataclass(frozen=True)
class Node:
    name: str
    heal: bool

    def __lt__(self, other):
        return self.name < other.name

    def __hash__(self):
        return super().__hash__()
    
    @property
    def is_resource_node(self) -> bool:
        return False

    def requirements_to_leave(self, patches: GamePatches, current_resources: CurrentResources) -> RequirementSet:
        return RequirementSet.trivial()


@dataclasses.dataclass(frozen=True)
class ResourceNode(Node):
    @property
    def is_resource_node(self) -> bool:
        return True

    def resource(self) -> ResourceInfo:
        raise NotImplementedError

    def can_collect(self, patches: GamePatches, current_resources: CurrentResources) -> bool:
        raise NotImplementedError

    def resource_gain_on_collect(self, patches: GamePatches, current_resources: CurrentResources) -> ResourceGain:
        raise NotImplementedError


@dataclasses.dataclass(frozen=True)
class GenericNode(Node):
    index: int


@dataclasses.dataclass(frozen=True)
class DockNode(Node):
    dock_index: int
    default_connection: DockConnection
    default_dock_weakness: DockWeakness

    def __repr__(self):
        return "DockNode({!r}/{} -> {})".format(self.name, self.dock_index, self.default_connection)


@dataclasses.dataclass(frozen=True)
class TeleporterNode(Node):
    teleporter_instance_id: int
    default_connection: AreaLocation

    def __repr__(self):
        return "TeleporterNode({!r} -> {})".format(self.name, self.default_connection)


@dataclasses.dataclass(frozen=True)
class PickupNode(ResourceNode):
    pickup_index: PickupIndex

    def __repr__(self):
        return "PickupNode({!r} -> {})".format(self.name, self.pickup_index.index)

    def resource(self) -> ResourceInfo:
        return self.pickup_index

    def can_collect(self, patches: GamePatches, current_resources: CurrentResources) -> bool:
        return current_resources.get(self.pickup_index, 0) == 0

    def resource_gain_on_collect(self, patches: GamePatches, current_resources: CurrentResources) -> ResourceGain:
        yield self.pickup_index, 1

        pickup = patches.pickup_assignment.get(self.pickup_index)
        if pickup is not None:
            yield from pickup.resource_gain(current_resources)


@dataclasses.dataclass(frozen=True)
class EventNode(ResourceNode):
    event: ResourceInfo

    def __repr__(self):
        return "EventNode({!r} -> {})".format(self.name, self.event.long_name)

    def resource(self) -> ResourceInfo:
        return self.event

    def can_collect(self, patches: GamePatches, current_resources) -> bool:
        return current_resources.get(self.event, 0) == 0

    def resource_gain_on_collect(self, patches: GamePatches, current_resources) -> ResourceGain:
        yield self.event, 1


@dataclasses.dataclass(frozen=True)
class TranslatorGateNode(ResourceNode):
    gate: TranslatorGate

    def __repr__(self):
        return "TranslatorGateNode({!r} -> {})".format(self.name, self.gate.index)

    def requirements_to_leave(self, patches: GamePatches, current_resources: CurrentResources) -> RequirementSet:
        return RequirementSet([
            RequirementList(0, [
                IndividualRequirement(patches.translator_gates[self.gate], 1, False)
            ])
        ])

    def resource(self) -> ResourceInfo:
        return self.gate

    def can_collect(self, patches: GamePatches, current_resources: CurrentResources) -> bool:
        """
        Checks if this TranslatorGate can be opened with the given resources and translator gate mapping
        :param patches:
        :param current_resources:
        :return:
        """
        return current_resources.get(patches.translator_gates[self.gate], 0) > 0

    def resource_gain_on_collect(self, patches: GamePatches, current_resources: CurrentResources) -> ResourceGain:
        yield self.gate, 1

