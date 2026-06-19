from __future__ import annotations

import base64
import typing

from randovania.bitpacking import bitpacking
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.network_common import pickup_serializer

if typing.TYPE_CHECKING:
    from collections.abc import Mapping
    from typing import Self

    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.lib.json_lib import JsonObject_RO


def _decode_pickup(d: str, resource_database: ResourceDatabase) -> PickupEntry:
    decoder = bitpacking.BitPackDecoder(base64.b85decode(d))
    return pickup_serializer.BitPackPickupEntry.bit_pack_unpack(decoder, {"database": resource_database}).value


def _base64_encode_pickup(pickup: PickupEntry, resource_database: ResourceDatabase) -> str:
    encoded_pickup = bitpacking.pack_value(pickup_serializer.BitPackPickupEntry(pickup, resource_database))
    return base64.b85encode(encoded_pickup).decode("utf-8")


class RemotePickup(typing.NamedTuple):
    provider_name: str
    pickup_entry: PickupEntry
    coop_location: PickupIndex | None

    @classmethod
    def from_json(cls, data: JsonObject_RO, resource_database: ResourceDatabase) -> Self:
        item = typing.cast("Mapping", data)
        return cls(
            item["provider_name"],
            _decode_pickup(item["pickup"], resource_database),
            PickupIndex(coop) if (coop := item["coop_location"]) is not None else None,
        )

    def as_json(self, resource_database: ResourceDatabase) -> JsonObject_RO:
        return {
            "provider_name": self.provider_name,
            "pickup": _base64_encode_pickup(self.pickup_entry, resource_database),
            "coop_location": self.coop_location.index if self.coop_location is not None else None,
        }
