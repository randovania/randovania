from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder, BitPackFloat
from randovania.game.game_enum import RandovaniaGame
from randovania.game_description.hint_features import HintFeature
from randovania.game_description.pickup.pickup_entry import (
    PickupEntry,
    PickupGeneratorParams,
    PickupModel,
    ResourceConversion,
    ResourceLock,
)
from randovania.game_description.resources.location_category import LocationCategory

if TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_description.resources.item_resource_info import ItemResourceInfo
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.game_description.resources.resource_info import ResourceQuantity

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
        amount = item[1]
        capacity = item[0].max_capacity
        assert abs(amount) <= capacity
        yield amount + capacity, capacity * 2 + 1

    def decode_resource_quantity(self, decoder: BitPackDecoder) -> ResourceQuantity:
        resource = self._decode_item(decoder)
        quantity = decoder.decode_single(resource.max_capacity * 2 + 1)
        return resource, quantity - resource.max_capacity

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
def _encode_hint_feature(feature: HintFeature):
    yield from bitpacking.encode_string(feature.name)
    yield from bitpacking.encode_string(feature.long_name)
    yield from bitpacking.encode_string(feature.hint_details[0])
    yield from bitpacking.encode_string(feature.hint_details[1])
    yield from bitpacking.encode_bool(feature.hidden)
    yield from bitpacking.encode_string(feature.description)


def _decode_hint_feature(decoder: BitPackDecoder) -> HintFeature:
    return HintFeature(
        name=bitpacking.decode_string(decoder),
        long_name=bitpacking.decode_string(decoder),
        hint_details=(bitpacking.decode_string(decoder), bitpacking.decode_string(decoder)),
        hidden=bitpacking.decode_bool(decoder),
        description=bitpacking.decode_string(decoder),
    )


class BitPackPickupEntry:
    value: PickupEntry
    database: ResourceDatabase

    def __init__(self, value: PickupEntry, database: ResourceDatabase):
        self.value = value
        self.database = database

    # Main Methods
    def bit_pack_encode(self, metadata) -> Iterator[tuple[int, int]]:
        helper = DatabaseBitPackHelper(self.database)

        yield from bitpacking.encode_string(self.value.name)
        yield from self.value.model.game.bit_pack_encode({})
        yield from bitpacking.encode_string(self.value.model.name)
        yield from _encode_hint_feature(self.value.gui_category)
        yield from bitpacking.encode_tuple(tuple(sorted(self.value.hint_features)), _encode_hint_feature)
        yield from bitpacking.encode_tuple(self.value.progression, helper.encode_resource_quantity)
        yield from bitpacking.encode_tuple(self.value.extra_resources, helper.encode_resource_quantity)
        yield from bitpacking.encode_bool(self.value.unlocks_resource)
        yield from bitpacking.encode_bool(self.value.resource_lock is not None)
        if self.value.resource_lock is not None:
            yield from helper.encode_resource_lock(self.value.resource_lock)
        yield from bitpacking.encode_bool(self.value.respects_lock)
        yield from self.value.generator_params.preferred_location_category.bit_pack_encode({})
        yield from BitPackFloat(self.value.generator_params.probability_offset).bit_pack_encode(
            _PROBABILITY_OFFSET_META
        )
        yield from BitPackFloat(self.value.generator_params.probability_multiplier).bit_pack_encode(
            _PROBABILITY_MULTIPLIER_META
        )
        yield from bitpacking.encode_big_int(self.value.generator_params.required_progression)
        yield from bitpacking.encode_bool(self.value.show_in_credits_spoiler)
        yield from bitpacking.encode_bool(self.value.is_expansion)

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, database: ResourceDatabase) -> PickupEntry:
        helper = DatabaseBitPackHelper(database)

        name = bitpacking.decode_string(decoder)
        model = PickupModel(
            game=RandovaniaGame.bit_pack_unpack(decoder, {}),
            name=bitpacking.decode_string(decoder),
        )
        pickup_category = _decode_hint_feature(decoder)
        hint_features = frozenset(bitpacking.decode_tuple(decoder, _decode_hint_feature))
        progression = bitpacking.decode_tuple(decoder, helper.decode_resource_quantity)
        extra_resources = bitpacking.decode_tuple(decoder, helper.decode_resource_quantity)
        unlocks_resource = bitpacking.decode_bool(decoder)
        resource_lock = None
        if bitpacking.decode_bool(decoder):
            resource_lock = helper.decode_resource_lock(decoder)
        respects_lock = bitpacking.decode_bool(decoder)

        location_category = LocationCategory.bit_pack_unpack(decoder, {})
        probability_offset = BitPackFloat.bit_pack_unpack(decoder, _PROBABILITY_OFFSET_META)
        probability_multiplier = BitPackFloat.bit_pack_unpack(decoder, _PROBABILITY_MULTIPLIER_META)
        required_progression = bitpacking.decode_big_int(decoder)

        show_in_credits_spoiler = bitpacking.decode_bool(decoder)
        is_expansion = bitpacking.decode_bool(decoder)

        return PickupEntry(
            name=name,
            model=model,
            gui_category=pickup_category,
            hint_features=hint_features,
            progression=progression,
            extra_resources=extra_resources,
            unlocks_resource=unlocks_resource,
            resource_lock=resource_lock,
            respects_lock=respects_lock,
            generator_params=PickupGeneratorParams(
                preferred_location_category=location_category,
                probability_offset=probability_offset,
                probability_multiplier=probability_multiplier,
                required_progression=required_progression,
            ),
            show_in_credits_spoiler=show_in_credits_spoiler,
            is_expansion=is_expansion,
        )
