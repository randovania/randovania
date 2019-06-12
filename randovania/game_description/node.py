import dataclasses
from enum import Enum
from typing import Optional

from randovania.game_description.area_location import AreaLocation
from randovania.game_description.dock import DockWeakness, DockConnection
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.requirements import RequirementSet, RequirementList, IndividualRequirement
from randovania.game_description.resources.logbook_asset import LogbookAsset
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_info import ResourceInfo, ResourceGain, CurrentResources
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.resources.translator_gate import TranslatorGate


@dataclasses.dataclass(frozen=True)
class Node:
    name: str
    heal: bool
    index: int

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
    pass


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

    def requirements_to_leave(self, patches: GamePatches, current_resources: CurrentResources) -> RequirementSet:
        if current_resources.get("add_self_as_requirement_to_resources") == 1:
            return RequirementSet([
                RequirementList(0, [
                    IndividualRequirement(self.pickup_index, 1, False),
                ])
            ])
        else:
            return RequirementSet.trivial()

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

    def requirements_to_leave(self, patches: GamePatches, current_resources: CurrentResources) -> RequirementSet:
        if current_resources.get("add_self_as_requirement_to_resources") == 1:
            return RequirementSet([
                RequirementList(0, [
                    IndividualRequirement(self.event, 1, False),
                ])
            ])
        else:
            return RequirementSet.trivial()

    def resource(self) -> ResourceInfo:
        return self.event

    def can_collect(self, patches: GamePatches, current_resources) -> bool:
        return current_resources.get(self.event, 0) == 0

    def resource_gain_on_collect(self, patches: GamePatches, current_resources) -> ResourceGain:
        yield self.event, 1


@dataclasses.dataclass(frozen=True)
class TranslatorGateNode(ResourceNode):
    gate: TranslatorGate
    scan_visor: SimpleResourceInfo

    def __repr__(self):
        return "TranslatorGateNode({!r} -> {})".format(self.name, self.gate.index)

    def requirements_to_leave(self, patches: GamePatches, current_resources: CurrentResources) -> RequirementSet:
        return RequirementSet([
            RequirementList(0, [
                IndividualRequirement(patches.translator_gates[self.gate], 1, False),
                IndividualRequirement(self.scan_visor, 1, False),
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
        if current_resources.get(self.gate, 0) != 0:
            return False
        translator = patches.translator_gates[self.gate]
        return current_resources.get(self.scan_visor, 0) > 0 and current_resources.get(translator, 0) > 0

    def resource_gain_on_collect(self, patches: GamePatches, current_resources: CurrentResources) -> ResourceGain:
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
    scan_visor: SimpleResourceInfo
    lore_type: LoreType
    required_translator: Optional[SimpleResourceInfo]
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

    def requirements_to_leave(self, patches: GamePatches, current_resources: CurrentResources) -> RequirementSet:
        items = [IndividualRequirement(self.scan_visor, 1, False)]
        if self.required_translator is not None:
            items.append(IndividualRequirement(self.required_translator, 1, False))

        return RequirementSet([RequirementList(0, items)])

    def resource(self) -> ResourceInfo:
        return LogbookAsset(self.string_asset_id)

    def can_collect(self, patches: GamePatches, current_resources: CurrentResources) -> bool:
        """
        Checks if this TranslatorGate can be opened with the given resources and translator gate mapping
        :param patches:
        :param current_resources:
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

    def resource_gain_on_collect(self, patches: GamePatches, current_resources: CurrentResources) -> ResourceGain:
        yield self.resource(), 1
