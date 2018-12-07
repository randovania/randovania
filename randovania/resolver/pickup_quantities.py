from typing import Dict, Optional, List, Tuple, Iterator

from randovania.bitpacking.bitpacking import BitPackDecoder, BitPackValue
from randovania.game_description.default_database import default_prime2_pickup_database
from randovania.game_description.resources import PickupDatabase, PickupEntry


class PickupQuantities(BitPackValue):
    _database: PickupDatabase
    _pickup_quantities: Dict[PickupEntry, int]
    _bit_pack_data: Optional[List[Tuple[int, int]]] = None

    def __init__(self, database: PickupDatabase, pickup_quantities: Dict[PickupEntry, int]):
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

        # print("zero count", len(zero_quantity_pickups))
        # print("one count", len(one_quantity_pickups))
        # print("many count", len(multiple_quantity_pickups))

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

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder) -> "PickupQuantities":
        pickup_database = default_prime2_pickup_database()

        pickup_list = list(pickup_database.pickups.values())
        total_pickup_count = pickup_database.total_pickup_count
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

    def items(self):
        return self._pickup_quantities.items()
