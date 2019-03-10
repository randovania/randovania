from dataclasses import dataclass
from typing import Iterator, Tuple

from randovania.bitpacking.bitpacking import BitPackDecoder, BitPackValue


@dataclass(frozen=True)
class PatcherConfiguration(BitPackValue):
    menu_mod: bool
    warp_to_start: bool

    @property
    def as_json(self) -> dict:
        return {
            "menu_mod": self.menu_mod,
            "warp_to_start": self.warp_to_start,
        }

    @classmethod
    def from_json_dict(cls, json_dict: dict) -> "PatcherConfiguration":
        return PatcherConfiguration(
            menu_mod=json_dict["menu_mod"],
            warp_to_start=json_dict["warp_to_start"],
        )

    @classmethod
    def default(cls) -> "PatcherConfiguration":
        return PatcherConfiguration(
            menu_mod=True,
            warp_to_start=True,
        )

    def bit_pack_encode(self) -> Iterator[Tuple[int, int]]:
        yield int(self.menu_mod), 2
        yield int(self.warp_to_start), 2

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder):
        menu_mod, warp_to_start = decoder.decode(2, 2)
        return cls(
            menu_mod=bool(menu_mod),
            warp_to_start=bool(warp_to_start),
        )
