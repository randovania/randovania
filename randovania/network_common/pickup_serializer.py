from typing import Iterator, Tuple

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackFloat, BitPackDecoder
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.resources.pickup_entry import PickupEntry, MAXIMUM_PICKUP_CONDITIONAL_RESOURCES, \
    MAXIMUM_PICKUP_RESOURCES, MAXIMUM_PICKUP_CONVERSION, ConditionalResources, ResourceConversion
from randovania.game_description.resources.resource_database import ResourceDatabase

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


class BitPackPickupEntry:
    value: PickupEntry
    database: ResourceDatabase

    def __init__(self, value: PickupEntry, database: ResourceDatabase):
        self.value = value
        self.database = database

    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        items = self.database.item

        yield from bitpacking.encode_string(self.value.name)
        yield self.value.model_index, 255
        yield from BitPackFloat(self.value.probability_offset).bit_pack_encode(_PROBABILITY_OFFSET_META)
        yield from BitPackFloat(self.value.probability_multiplier).bit_pack_encode(_PROBABILITY_MULTIPLIER_META)
        yield from self.value.item_category.bit_pack_encode({})
        yield from self.value.broad_category.bit_pack_encode({})
        yield len(self.value.resources) - 1, MAXIMUM_PICKUP_CONDITIONAL_RESOURCES

        for i, conditional in enumerate(self.value.resources):
            if i > 0:
                yield from bitpacking.pack_array_element(conditional.item, items)

            yield len(conditional.resources), MAXIMUM_PICKUP_RESOURCES + 1
            for resource, quantity in conditional.resources:
                yield from bitpacking.pack_array_element(resource, items)
                yield quantity, 255

            yield from bitpacking.encode_bool(conditional.name is not None)
            if conditional.name is not None:
                yield from bitpacking.encode_string(conditional.name)

        yield len(self.value.convert_resources), MAXIMUM_PICKUP_CONVERSION + 1
        for conversion in self.value.convert_resources:
            yield from bitpacking.pack_array_element(conversion.source, items)
            yield from bitpacking.pack_array_element(conversion.target, items)

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, database: ResourceDatabase) -> PickupEntry:
        name = bitpacking.decode_string(decoder)
        model_index = decoder.decode_single(255)
        probability_offset = BitPackFloat.bit_pack_unpack(decoder, _PROBABILITY_OFFSET_META)
        probability_multiplier = BitPackFloat.bit_pack_unpack(decoder, _PROBABILITY_MULTIPLIER_META)
        item_category = ItemCategory.bit_pack_unpack(decoder, {})
        broad_category = ItemCategory.bit_pack_unpack(decoder, {})
        num_conditional = decoder.decode_single(MAXIMUM_PICKUP_CONDITIONAL_RESOURCES) + 1

        conditional_resources = []
        for i in range(num_conditional):
            item_name = None  # TODO: get the first resource name
            if i > 0:
                item_dependency = decoder.decode_element(database.item)
            else:
                item_dependency = None

            resources = []
            for _ in range(decoder.decode_single(MAXIMUM_PICKUP_RESOURCES + 1)):
                resource = decoder.decode_element(database.item)
                quantity = decoder.decode_single(255)
                resources.append((resource, quantity))

            if bitpacking.decode_bool(decoder):
                item_name = bitpacking.decode_string(decoder)

            conditional_resources.append(ConditionalResources(
                name=item_name,
                item=item_dependency,
                resources=tuple(resources),
            ))

        num_convert = decoder.decode_single(MAXIMUM_PICKUP_CONVERSION + 1)
        convert_resources = []
        for i in range(num_convert):
            source = decoder.decode_element(database.item)
            target = decoder.decode_element(database.item)
            convert_resources.append(ResourceConversion(source, target))

        return PickupEntry(
            name=name,
            model_index=model_index,
            item_category=item_category,
            broad_category=broad_category,
            resources=tuple(conditional_resources),
            convert_resources=tuple(convert_resources),
            probability_offset=probability_offset,
            probability_multiplier=probability_multiplier,
        )
