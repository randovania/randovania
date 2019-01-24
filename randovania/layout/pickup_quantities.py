from typing import Dict, Optional, List, Tuple, Iterator

from randovania.bitpacking.bitpacking import BitPackDecoder, BitPackValue
from randovania.game_description.default_database import default_prime2_pickup_database
from randovania.game_description.resources import PickupDatabase, PickupEntry


class PickupQuantities(BitPackValue):
    _database: PickupDatabase
    _pickup_quantities: Dict[PickupEntry, int]
    _bit_pack_data: Optional[List[Tuple[int, int]]] = None

    def __init__(self, database: PickupDatabase, pickup_quantities: Dict[PickupEntry, int]):
        assert database.useless_pickup not in pickup_quantities
        self._database = database
        self._pickup_quantities = pickup_quantities

    def __repr__(self):
        return "PickupQuantities({})".format(repr({
            item.name: quantity
            for item, quantity in self.pickups_with_custom_quantities.items()
        }))

    def _calculate_bit_pack(self):
        if self._bit_pack_data is not None:
            return
        bit_pack_data = []

        if not self.pickups_with_custom_quantities:
            # Default configuration, don't pack anything
            self._bit_pack_data = bit_pack_data
            return

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

        pickup_list = list(self._database.all_useful_pickups)
        total_pickup_count = self._database.total_pickup_count

        bit_pack_data.append((len(pickup_list), len(zero_quantity_pickups)))
        bit_pack_data.append((len(pickup_list) - len(zero_quantity_pickups), len(one_quantity_pickups)))

        # print("zero count", len(zero_quantity_pickups))
        # print("one count", len(one_quantity_pickups))
        # print("many count", len(multiple_quantity_pickups))

        # print("zero!")

        for pickup in zero_quantity_pickups:
            bit_pack_data.append((len(pickup_list), pickup_list.index(pickup)))
            # print(self._bit_pack_data[-1])
            pickup_list.remove(pickup)

        # print("many!")

        for pickup in multiple_quantity_pickups:
            bit_pack_data.append((len(pickup_list), pickup_list.index(pickup)))
            pickup_list.remove(pickup)
            # print(self._bit_pack_data[-1])

            quantity = self._pickup_quantities[pickup]
            if total_pickup_count != quantity:
                bit_pack_data.append((total_pickup_count, quantity))
                # print("!!!", self._bit_pack_data[-1])
            total_pickup_count -= quantity

        # print("one!")
        if not (total_pickup_count >= len(one_quantity_pickups) == len(pickup_list)):
            self.validate_total_quantities()
            raise ValueError("Unable to pack PickupQuantities: total {}, ones: {}, list_size: {}".format(
                total_pickup_count, len(one_quantity_pickups), len(pickup_list)
            ))

        self._bit_pack_data = bit_pack_data

    def bit_pack_format(self) -> Iterator[int]:
        self._calculate_bit_pack()
        yield 2
        for item in self._bit_pack_data:
            yield item[0]

    def bit_pack_arguments(self) -> Iterator[int]:
        self._calculate_bit_pack()
        yield 1 if self._bit_pack_data else 0
        for item in self._bit_pack_data:
            yield item[1]

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder) -> "PickupQuantities":
        pickup_database = default_prime2_pickup_database()

        pickup_list = list(pickup_database.all_useful_pickups)
        total_pickup_count = pickup_database.total_pickup_count

        has_custom_quantities = bool(decoder.decode(2)[0])
        if not has_custom_quantities:
            return PickupQuantities(pickup_database, {})._add_missing_pickups_to_quantities()

        pickup_quantities = {}

        zero_quantity_pickups = decoder.decode(len(pickup_list))[0]
        one_quantity_pickups = decoder.decode(len(pickup_list) - zero_quantity_pickups)[0]
        multiple_quantity_pickups = len(pickup_list) - zero_quantity_pickups - one_quantity_pickups

        # zero
        for _ in range(zero_quantity_pickups):
            index = decoder.decode(len(pickup_list))[0]
            pickup_quantities[pickup_list.pop(index)] = 0

        # multi
        for i in range(multiple_quantity_pickups):
            index = decoder.decode(len(pickup_list))[0]
            if i != multiple_quantity_pickups - 1 or one_quantity_pickups > 0:
                quantity = decoder.decode(total_pickup_count)[0]
            else:
                quantity = total_pickup_count
            pickup_quantities[pickup_list.pop(index)] = quantity
            total_pickup_count -= quantity

        # one
        assert len(pickup_list) == one_quantity_pickups
        for one_pickup in pickup_list:
            pickup_quantities[one_pickup] = 1

        return PickupQuantities(pickup_database, pickup_quantities)

    def __eq__(self, other):
        return isinstance(other, PickupQuantities) and self._pickup_quantities == other._pickup_quantities

    def __iter__(self):
        return iter(self._pickup_quantities)

    def get(self, pickup: PickupEntry) -> int:
        return self._pickup_quantities[pickup]

    def pickups(self) -> Iterator[PickupEntry]:
        yield from self._pickup_quantities.keys()

    def items(self):
        return self._pickup_quantities.items()

    @property
    def pickups_with_custom_quantities(self) -> Dict[PickupEntry, int]:
        return {
            pickup: quantity
            for pickup, quantity in self._pickup_quantities.items()
            if self._database.original_quantity_for(pickup) != quantity
        }

    @property
    def as_json(self) -> dict:
        return {
            pickup.name: quantity
            for pickup, quantity in self._pickup_quantities.items()
            if self._database.original_quantity_for(pickup) != quantity
        }

    @classmethod
    def from_params(cls, pickup_quantities: Dict[str, int]) -> "PickupQuantities":
        pickup_database = default_prime2_pickup_database()
        quantities = {
            pickup_database.pickup_by_name(name): quantity
            for name, quantity in pickup_quantities.items()
        }
        return PickupQuantities(pickup_database, quantities)._add_missing_pickups_to_quantities()

    def with_new_quantities(self, pickup_quantities: Dict[PickupEntry, int]) -> "PickupQuantities":
        return PickupQuantities(self._database, pickup_quantities)._add_missing_pickups_to_quantities()

    def _add_missing_pickups_to_quantities(self) -> "PickupQuantities":
        for pickup in self._database.all_useful_pickups:
            if pickup not in self._pickup_quantities:
                self._pickup_quantities[pickup] = self._database.original_quantity_for(pickup)

        return self

    def validate_total_quantities(self):
        total = sum(self._pickup_quantities.values())
        if total > self._database.total_pickup_count:
            raise ValueError(
                "Invalid pickup_quantities. \n{} implies into more than {} pickups".format(
                    self.as_json,
                    self._database.total_pickup_count
                ))
