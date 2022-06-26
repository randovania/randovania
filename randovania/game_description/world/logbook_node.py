import dataclasses
from enum import Enum

from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.node_resource_info import NodeResourceInfo
from randovania.game_description.resources.resource_info import ResourceGain
from randovania.game_description.world.node import NodeContext
from randovania.game_description.world.resource_node import ResourceNode


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


@dataclasses.dataclass(frozen=True, slots=True)
class LogbookNode(ResourceNode):
    string_asset_id: int
    scan_visor: ItemResourceInfo | None
    lore_type: LoreType
    required_translator: ItemResourceInfo | None
    hint_index: int | None

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

    def requirement_to_leave(self, context: NodeContext) -> Requirement:
        items = []
        if self.scan_visor is not None:
            items.append(ResourceRequirement.simple(self.scan_visor))
        if self.required_translator is not None:
            items.append(ResourceRequirement.simple(self.required_translator))

        return RequirementAnd(items)

    def resource(self, context: NodeContext) -> NodeResourceInfo:
        return NodeResourceInfo.from_node(self, context)

    def can_collect(self, context: NodeContext) -> bool:
        """
        Checks if this TranslatorGate can be opened with the given resources and translator gate mapping
        :param context:
        :return:
        """
        current_resources = context.current_resources
        if self.is_collected(context):
            return False

        if self.scan_visor is not None:
            if not current_resources.has_resource(self.scan_visor):
                return False

        if self.required_translator is not None:
            return current_resources.has_resource(self.required_translator)

        return True

    def is_collected(self, context: NodeContext) -> bool:
        return context.has_resource(self.resource(context))

    def resource_gain_on_collect(self, context: NodeContext) -> ResourceGain:
        yield self.resource(context), 1
