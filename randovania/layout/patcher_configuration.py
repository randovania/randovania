from dataclasses import dataclass
from typing import Iterator

from randovania.bitpacking.bitpacking import BitPackDecoder


@dataclass(frozen=True)
class PatcherConfiguration:
    menu_mod: bool

    @property
    def as_json(self) -> dict:
        return {
            "menu_mod": self.menu_mod,
        }

    @classmethod
    def from_json_dict(cls, json_dict: dict) -> "PatcherConfiguration":
        return PatcherConfiguration(
            menu_mod=json_dict["menu_mod"],
        )

    @classmethod
    def default(cls) -> "PatcherConfiguration":
        return PatcherConfiguration(
            menu_mod=True,
        )

    def bit_pack_format(self) -> Iterator[int]:
        yield 2

    def bit_pack_arguments(self) -> Iterator[int]:
        yield int(self.menu_mod)

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder):
        menu_mod = decoder.decode(2)
        return cls(
            menu_mod=bool(menu_mod),
        )
