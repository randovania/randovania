from dataclasses import dataclass
from typing import Optional, Tuple, Iterator

from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.resource_info import ResourceGainTuple, ResourceGain, ResourceQuantity
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo


@dataclass(frozen=True)
class ConditionalResources:
    name: Optional[str]
    item: Optional[ItemResourceInfo]
    resources: ResourceGainTuple


@dataclass(frozen=True)
class ResourceConversion:
    source: ItemResourceInfo
    target: ItemResourceInfo
    clear_source: bool = True
    overwrite_target: bool = False


MAXIMUM_PICKUP_CONDITIONAL_RESOURCES = 3
MAXIMUM_PICKUP_RESOURCES = 8
MAXIMUM_PICKUP_CONVERSION = 2


@dataclass(frozen=True)
class PickupEntry:
    name: str
    model_index: int
    item_category: ItemCategory
    broad_category: ItemCategory
    resources: Tuple[ConditionalResources, ...]
    convert_resources: Tuple[ResourceConversion, ...] = tuple()
    probability_offset: float = 0
    probability_multiplier: float = 1

    def __post_init__(self):
        if not isinstance(self.resources, tuple):
            raise ValueError("resources should be a tuple, got {}".format(self.resources))

        if len(self.resources) < 1:
            raise ValueError("resources should have at least 1 value")

        if len(self.resources) > MAXIMUM_PICKUP_CONDITIONAL_RESOURCES:
            raise ValueError(f"resources should have at most {MAXIMUM_PICKUP_CONDITIONAL_RESOURCES} "
                             f"values, got {len(self.resources)}")

        for i, conditional in enumerate(self.resources):
            if not isinstance(conditional, ConditionalResources):
                raise ValueError(f"Conditional at {i} should be a ConditionalResources")

            if len(conditional.resources) > MAXIMUM_PICKUP_RESOURCES:
                raise ValueError(f"Conditional at {i} should have at most {MAXIMUM_PICKUP_RESOURCES} "
                                 f"resources, got {len(conditional.resources)}")

            if i == 0:
                if conditional.item is not None:
                    raise ValueError("Conditional at 0 should not have a condition")
            else:
                if conditional.item is None:
                    raise ValueError(f"Conditional at {i} should have a condition")

        if len(self.convert_resources) > MAXIMUM_PICKUP_CONVERSION:
            raise ValueError(f"convert_resources should have at most {MAXIMUM_PICKUP_CONVERSION} value")

        for i, conversion in enumerate(self.convert_resources):
            if not conversion.clear_source or conversion.overwrite_target:
                raise ValueError(f"clear_source and overwrite_target should be True and False, "
                                 f"got {conversion.clear_source} and {conversion.overwrite_target} for index {i}")

    def __hash__(self):
        return hash(self.name)

    def __lt__(self, other):
        return self.name < other.name

    def conditional_for_resources(self, current_resources) -> ConditionalResources:
        last_conditional: Optional[ConditionalResources] = None

        for conditional in self.resources:
            if conditional.item is None or current_resources.get(conditional.item, 0) > 0:
                last_conditional = conditional
            else:
                break

        assert last_conditional is not None
        return last_conditional

    def conversion_resource_gain(self, current_resources):
        for conversion in self.convert_resources:
            quantity = current_resources.get(conversion.source, 0)
            yield conversion.source, -quantity
            yield conversion.target, quantity

    def resource_gain(self, current_resources) -> ResourceGain:
        yield from self.conditional_for_resources(current_resources).resources
        yield from self.conversion_resource_gain(current_resources)

    def __str__(self):
        return "Pickup {}".format(self.name)

    @property
    def all_resources(self) -> Iterator[ResourceQuantity]:
        for conditional in self.resources:
            yield from conditional.resources

    @property
    def is_expansion(self) -> bool:
        return self.item_category == ItemCategory.EXPANSION
