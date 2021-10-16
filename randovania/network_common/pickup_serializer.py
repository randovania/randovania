from randovania.game_description.item.item_category import ItemCategory
from typing import Iterator, Tuple

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackFloat, BitPackDecoder
from randovania.game_description import default_database
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_entry import PickupEntry, ResourceConversion, ResourceLock, \
    PickupModel
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceQuantity
from randovania.games.game import RandovaniaGame

_PROBABILITY_OFFSET_META = {
    "min": -3,
    "max": 3,
    "precision": 2.0,
    "if_different": 0.0,
}
_PROBABILITY_MULTIPLIER_META = {
    "min": 0,
    "max": 8,
    "precision": 2.0,
    "if_different": 1.0,
}


class DatabaseBitPackHelper:
    def __init__(self, database: ResourceDatabase):
        self.database = database

    def _decode_item(self, decoder: BitPackDecoder) -> ItemResourceInfo:
        return decoder.decode_element(self.database.item)

    # Resource Quantity
    def encode_resource_quantity(self, item: ResourceQuantity):
        yield from bitpacking.pack_array_element(item[0], self.database.item)
        assert item[1] <= item[0].max_capacity
        yield item[1], item[0].max_capacity + 1

    def decode_resource_quantity(self, decoder: BitPackDecoder) -> ResourceQuantity:
        resource = self._decode_item(decoder)
        quantity = decoder.decode_single(resource.max_capacity + 1)
        return resource, quantity

    # Resource Conversion
    def encode_resource_conversion(self, item: ResourceConversion):
        yield from bitpacking.pack_array_element(item.source, self.database.item)
        yield from bitpacking.pack_array_element(item.target, self.database.item)

    def decode_resource_conversion(self, decoder: BitPackDecoder) -> ResourceConversion:
        return ResourceConversion(
            source=self._decode_item(decoder),
            target=self._decode_item(decoder),
        )

    # Resource Lock
    def encode_resource_lock(self, lock: ResourceLock):
        yield from bitpacking.pack_array_element(lock.locked_by, self.database.item)
        yield from bitpacking.pack_array_element(lock.item_to_lock, self.database.item)
        yield from bitpacking.pack_array_element(lock.temporary_item, self.database.item)

    def decode_resource_lock(self, decoder: BitPackDecoder) -> ResourceLock:
        return ResourceLock(
            locked_by=self._decode_item(decoder),
            item_to_lock=self._decode_item(decoder),
            temporary_item=self._decode_item(decoder),
        )

# Item categories encoding & decoding
def _encode_item_category(category: ItemCategory):
    yield from bitpacking.encode_string(category.name)
    yield from bitpacking.encode_string(category.long_name)
    yield from bitpacking.encode_string(category.hint_details[0])
    yield from bitpacking.encode_string(category.hint_details[1])
    yield from bitpacking.encode_bool(category.is_major)
    yield from bitpacking.encode_bool(category.is_key)

def _decode_item_category(decoder: BitPackDecoder) -> ItemCategory:
    return ItemCategory(
        name=bitpacking.decode_string(decoder),
        long_name=bitpacking.decode_string(decoder),
        hint_details=(bitpacking.decode_string(decoder), bitpacking.decode_string(decoder)),
        is_major=bitpacking.decode_bool(decoder),
        is_key=bitpacking.decode_bool(decoder)
    )


class BitPackPickupEntry:
    value: PickupEntry
    database: ResourceDatabase
    
    def __init__(self, value: PickupEntry, database: ResourceDatabase):
        self.value = value
        self.database = database

    # Main Methods
    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        helper = DatabaseBitPackHelper(self.database)

        yield from bitpacking.encode_string(self.value.name)
        yield from self.value.model.game.bit_pack_encode({})
        yield from bitpacking.encode_string(self.value.model.name)
        yield from _encode_item_category(self.value.item_category)
        yield from _encode_item_category(self.value.broad_category)
        yield from bitpacking.encode_tuple(self.value.progression, helper.encode_resource_quantity)
        yield from bitpacking.encode_tuple(self.value.extra_resources, helper.encode_resource_quantity)
        yield from bitpacking.encode_bool(self.value.unlocks_resource)
        yield from bitpacking.encode_bool(self.value.resource_lock is not None)
        if self.value.resource_lock is not None:
            yield from helper.encode_resource_lock(self.value.resource_lock)
        yield from bitpacking.encode_bool(self.value.respects_lock)
        yield from BitPackFloat(self.value.probability_offset).bit_pack_encode(_PROBABILITY_OFFSET_META)
        yield from BitPackFloat(self.value.probability_multiplier).bit_pack_encode(_PROBABILITY_MULTIPLIER_META)
        yield from bitpacking.encode_big_int(self.value.required_progression)

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, database: ResourceDatabase) -> PickupEntry:
        helper = DatabaseBitPackHelper(database)

        name = bitpacking.decode_string(decoder)
        model = PickupModel(
            game=RandovaniaGame.bit_pack_unpack(decoder, {}),
            name=bitpacking.decode_string(decoder),
        )
        item_category = _decode_item_category(decoder)
        broad_category = _decode_item_category(decoder)
        progression = bitpacking.decode_tuple(decoder, helper.decode_resource_quantity)
        extra_resources = bitpacking.decode_tuple(decoder, helper.decode_resource_quantity)
        unlocks_resource = bitpacking.decode_bool(decoder)
        resource_lock = None
        if bitpacking.decode_bool(decoder):
            resource_lock = helper.decode_resource_lock(decoder)
        respects_lock = bitpacking.decode_bool(decoder)
        probability_offset = BitPackFloat.bit_pack_unpack(decoder, _PROBABILITY_OFFSET_META)
        probability_multiplier = BitPackFloat.bit_pack_unpack(decoder, _PROBABILITY_MULTIPLIER_META)
        required_progression = bitpacking.decode_big_int(decoder)

        return PickupEntry(
            name=name,
            model=model,
            item_category=item_category,
            broad_category=broad_category,
            progression=progression,
            extra_resources=extra_resources,
            unlocks_resource=unlocks_resource,
            resource_lock=resource_lock,
            respects_lock=respects_lock,
            probability_offset=probability_offset,
            probability_multiplier=probability_multiplier,
            required_progression=required_progression,
        )
