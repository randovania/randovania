from dataclasses import dataclass
from typing import Iterator

from randovania.bitpacking.bitpacking import BitPackDecoder


@dataclass(frozen=True)
class PatcherConfiguration:
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

    def bit_pack_format(self) -> Iterator[int]:
        yield 2
        yield 2

    def bit_pack_arguments(self) -> Iterator[int]:
        yield int(self.menu_mod)
        yield int(self.warp_to_start)

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder):
        menu_mod, warp_to_start = decoder.decode(2, 2)
        return cls(
            menu_mod=bool(menu_mod),
            warp_to_start=bool(warp_to_start),
        )
