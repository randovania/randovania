from dataclasses import dataclass
from typing import Optional, Iterator, Tuple

from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.resource_info import ResourceGainTuple, ResourceGain, ResourceQuantity, \
    CurrentResources
from randovania.games.game import RandovaniaGame


@dataclass(frozen=True)
class ResourceConversion:
    source: ItemResourceInfo
    target: ItemResourceInfo
    clear_source: bool = True
    overwrite_target: bool = False


@dataclass(frozen=True)
class ResourceLock:
    locked_by: ItemResourceInfo
    item_to_lock: ItemResourceInfo
    temporary_item: ItemResourceInfo

    def convert_gain(self, gain: ResourceGain) -> ResourceGain:
        for resource, quantity in gain:
            if self.item_to_lock == resource:
                resource = self.temporary_item
            yield resource, quantity

    def unlock_conversion(self) -> ResourceConversion:
        return ResourceConversion(source=self.temporary_item,
                                  target=self.item_to_lock)


@dataclass(frozen=True)
class ConditionalResources:
    name: Optional[str]
    item: Optional[ItemResourceInfo]
    resources: ResourceGainTuple


@dataclass(frozen=True)
class PickupModel:
    game: RandovaniaGame
    name: str


@dataclass(frozen=True)
class PickupEntry:
    name: str
    model: PickupModel
    item_category: ItemCategory
    broad_category: ItemCategory
    progression: ResourceGainTuple
    extra_resources: ResourceGainTuple = tuple()
    unlocks_resource: bool = False
    resource_lock: Optional[ResourceLock] = None
    respects_lock: bool = True
    probability_offset: float = 0
    probability_multiplier: float = 1

    def __post_init__(self):
        if not isinstance(self.progression, tuple):
            raise ValueError("resources should be a tuple, got {}".format(self.progression))

        for i, progression in enumerate(self.progression):
            if not isinstance(progression, tuple):
                raise ValueError(f"{i}-th progression should be a tuple, got {progression}")

            if len(progression) != 2:
                raise ValueError(f"{i}-th progression should have 2 elements, got {len(progression)}")

            if not isinstance(progression[1], int):
                raise ValueError(f"{i}-th progression second field should be a int, got {progression[1]}")

            if progression[1] > progression[0].max_capacity:
                raise ValueError(f"{i}-th progression has {progression[1]} quantity, "
                                 f"higher than max for {progression[0]}")

        for resource, quantity in self.extra_resources:
            if isinstance(resource, ItemResourceInfo):
                if quantity > resource.max_capacity:
                    raise ValueError(f"Attempt to give {quantity} of {resource.long_name}, more than max capacity")

    def __hash__(self):
        return hash(self.name)

    def __lt__(self, other):
        return self.name < other.name

    @property
    def conditional_resources(self):
        previous: Optional[ItemResourceInfo] = None
        for progression in self.progression:
            yield ConditionalResources(
                name=progression[0].long_name,
                item=previous,
                resources=(progression,) + self.extra_resources,
            )
            previous = progression[0]

        if not self.progression:
            yield ConditionalResources(
                name=self.name,
                item=None,
                resources=self.extra_resources,
            )

    @property
    def convert_resources(self) -> Tuple[ResourceConversion, ...]:
        if self.unlocks_resource and self.resource_lock is not None:
            return (self.resource_lock.unlock_conversion(),)
        else:
            return tuple()

    def conditional_for_resources(self, current_resources: CurrentResources) -> ConditionalResources:
        last_conditional: Optional[ConditionalResources] = None

        for conditional in self.conditional_resources:
            if conditional.item is None or current_resources.get(conditional.item, 0) > 0:
                last_conditional = conditional
            else:
                break

        assert last_conditional is not None
        return last_conditional

    def conversion_resource_gain(self, current_resources: CurrentResources) -> ResourceGain:
        for conversion in self.convert_resources:
            quantity = current_resources.get(conversion.source, 0)
            yield conversion.source, -quantity
            yield conversion.target, quantity

    def resource_gain(self, current_resources: CurrentResources, force_lock: bool = False) -> ResourceGain:
        resources = self.conditional_for_resources(current_resources).resources

        if (force_lock or self.respects_lock) and not self.unlocks_resource and (
                self.resource_lock is not None and current_resources.get(self.resource_lock.locked_by, 0) == 0):
            yield from self.resource_lock.convert_gain(resources)
        else:
            yield from resources

        yield from self.conversion_resource_gain(current_resources)

    def __str__(self):
        return "Pickup {}".format(self.name)

    @property
    def all_resources(self) -> Iterator[ResourceQuantity]:
        yield from self.progression
        yield from self.extra_resources

    @property
    def is_expansion(self) -> bool:
        return self.item_category == ItemCategory.EXPANSION
