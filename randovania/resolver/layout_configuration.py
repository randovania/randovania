import dataclasses
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Iterator, Dict, Tuple

from randovania.bitpacking.bitpacking import BitPackValue
from randovania.game_description.default_database import default_prime2_pickup_database
from randovania.game_description.resources import PickupEntry, PickupDatabase


class BitPackEnum(BitPackValue):
    def bit_pack_format(self) -> Iterator[int]:
        cls: Enum = self.__class__
        yield len(cls.__members__)

    def bit_pack_arguments(self) -> Iterator[int]:
        cls: Enum = self.__class__
        yield list(cls.__members__.values()).index(self)


class BitPackDataClass(BitPackValue):
    def bit_pack_format(self) -> Iterator[int]:
        for field in dataclasses.fields(self):
            yield from getattr(self, field.name).bit_pack_format()

    def bit_pack_arguments(self) -> Iterator[int]:
        for field in dataclasses.fields(self):
            yield from getattr(self, field.name).bit_pack_arguments()


class LayoutTrickLevel(BitPackEnum, Enum):
    NO_TRICKS = "no-tricks"
    TRIVIAL = "trivial"
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    HYPERMODE = "hypermode"
    MINIMAL_RESTRICTIONS = "minimal-restrictions"


class LayoutMode(BitPackEnum, Enum):
    STANDARD = "standard"
    MAJOR_ITEMS = "major-items"


class LayoutRandomizedFlag(BitPackEnum, Enum):
    VANILLA = "vanilla"
    RANDOMIZED = "randomized"


class LayoutEnabledFlag(BitPackEnum, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"


class LayoutDifficulty(BitPackEnum, Enum):
    NORMAL = "normal"


class PickupQuantities:
    _database: PickupDatabase
    _pickup_quantities: Dict[PickupEntry, int]
    _bit_pack_data: Optional[List[Tuple[int, int]]] = None

    def __init__(self, database: PickupDatabase, pickup_quantities: Dict[str, int]):
        self._database = database
        self._pickup_quantities = pickup_quantities

    def _calculate_bit_pack(self):
        if self._bit_pack_data is not None:
            return
        self._bit_pack_data = []

        zero_quantity_pickups = []
        one_quantity_pickups = []
        multiple_quantity_pickups = []

        for pickup, quantity in sorted(self._pickup_quantities.items(), key=lambda x: x[1], reverse=True):
            if quantity == 0:
                array = zero_quantity_pickups
            elif quantity == 1:
                array = one_quantity_pickups
            else:
                array = multiple_quantity_pickups
            array.append(pickup)

        pickup_list = list(self._database.pickups.values())
        total_pickup_count = self._database.total_pickup_count

        self._bit_pack_data.append((len(pickup_list), len(zero_quantity_pickups)))
        self._bit_pack_data.append((len(pickup_list) - len(zero_quantity_pickups), len(one_quantity_pickups)))

        # print("zero!")

        for pickup in zero_quantity_pickups:
            self._bit_pack_data.append((len(pickup_list), pickup_list.index(pickup)))
            # print(self._bit_pack_data[-1])
            pickup_list.remove(pickup)

        # print("many!")

        for pickup in multiple_quantity_pickups:
            self._bit_pack_data.append((len(pickup_list), pickup_list.index(pickup)))
            pickup_list.remove(pickup)
            # print(self._bit_pack_data[-1])

            quantity = self._pickup_quantities[pickup]
            if total_pickup_count != quantity:
                self._bit_pack_data.append((total_pickup_count, quantity))
                # print("!!!", self._bit_pack_data[-1])
            total_pickup_count -= quantity

        # print("one!")
        assert total_pickup_count >= len(one_quantity_pickups) == len(pickup_list)

    def bit_pack_format(self) -> Iterator[int]:
        self._calculate_bit_pack()
        for item in self._bit_pack_data:
            yield item[0]

    def bit_pack_arguments(self) -> Iterator[int]:
        self._calculate_bit_pack()
        for item in self._bit_pack_data:
            yield item[1]

    def __eq__(self, other):
        return isinstance(other, PickupQuantities) and self._pickup_quantities == other._pickup_quantities

    def __iter__(self):
        return iter(self._pickup_quantities)

    def get(self, pickup: PickupEntry) -> int:
        return self._pickup_quantities[pickup]

    def items(self):
        return self._pickup_quantities.items()


@dataclass(frozen=True)
class LayoutConfiguration(BitPackDataClass):
    trick_level: LayoutTrickLevel
    sky_temple_keys: LayoutRandomizedFlag
    item_loss: LayoutEnabledFlag
    elevators: LayoutRandomizedFlag
    pickup_quantities: PickupQuantities

    def quantity_for_pickup(self, pickup: PickupEntry) -> Optional[int]:
        return self.pickup_quantities.get(pickup)

    @property
    def as_json(self) -> dict:
        return {
            "game": "mp2-echoes",
            "trick_level": self.trick_level.value,
            "sky_temple_keys": self.sky_temple_keys.value,
            "item_loss": self.item_loss.value,
            "elevators": self.elevators.value,
            "pickup_quantities": {
                pickup.name: quantity
                for pickup, quantity in self.pickup_quantities.items()
            },
        }

    @property
    def as_str(self) -> str:
        strings: List[str] = [self.trick_level.value]

        if self.sky_temple_keys == LayoutRandomizedFlag.VANILLA:
            strings.append("vanilla-sky-temple-keys")

        if self.item_loss == LayoutEnabledFlag.DISABLED:
            strings.append("disabled-item-loss")

        if self.elevators == LayoutRandomizedFlag.RANDOMIZED:
            strings.append("randomized-elevators")

        if self.pickup_quantities:
            strings.append("customized-quantities")

        return "_".join(strings)

    @classmethod
    def from_json_dict(cls, json_dict: dict) -> "LayoutConfiguration":
        return cls.from_params(
            trick_level=LayoutTrickLevel(json_dict["trick_level"]),
            sky_temple_keys=LayoutRandomizedFlag(json_dict["sky_temple_keys"]),
            item_loss=LayoutEnabledFlag(json_dict["item_loss"]),
            elevators=LayoutRandomizedFlag(json_dict["elevators"]),
            pickup_quantities=json_dict["pickup_quantities"],
        )

    @classmethod
    def from_params(cls,
                    trick_level: LayoutTrickLevel,
                    sky_temple_keys: LayoutRandomizedFlag,
                    item_loss: LayoutEnabledFlag,
                    elevators: LayoutRandomizedFlag,
                    pickup_quantities: Dict[str, int],
                    ) -> "LayoutConfiguration":

        pickup_database = default_prime2_pickup_database()

        quantities = {
            pickup: pickup_database.original_quantity_for(pickup)
            for pickup in pickup_database.pickups.values()
        }
        for name, quantity in pickup_quantities.items():
            quantities[pickup_database.pickup_by_name(name)] = quantity

        if sum(quantities.values()) > pickup_database.total_pickup_count:
            raise ValueError(
                "Invalid pickup_quantities. {} along with unmapped original pickups sum to more than {}".format(
                    pickup_quantities, pickup_database.total_pickup_count
                ))

        return LayoutConfiguration(
            trick_level=trick_level,
            sky_temple_keys=sky_temple_keys,
            item_loss=item_loss,
            elevators=elevators,
            pickup_quantities=PickupQuantities(pickup_database, quantities)
        )


@dataclass(frozen=True)
class Permalink:
    seed_number: int
    configuration: LayoutConfiguration

    @classmethod
    def current_version(cls) -> int:
        return 0

    def bit_pack_format(self) -> Iterator[int]:
        yield 16
        yield 2 ** 31
        yield from self.configuration.bit_pack_format()

    def bit_pack_arguments(self) -> Iterator[int]:
        yield self.current_version()
        yield self.seed_number
        yield from self.configuration.bit_pack_arguments()
