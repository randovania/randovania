from dataclasses import dataclass
from typing import Iterator

from randovania.bitpacking.bitpacking import BitPackDecoder


@dataclass(frozen=True)
class PatcherConfiguration:
    disable_hud_popup: bool
    menu_mod: bool

    @property
    def as_json(self) -> dict:
        return {
            "disable_hud_popup": self.disable_hud_popup,
            "menu_mod": self.menu_mod,
        }

    @classmethod
    def from_json_dict(cls, json_dict: dict) -> "PatcherConfiguration":
        return PatcherConfiguration(
            disable_hud_popup=json_dict["disable_hud_popup"],
            menu_mod=json_dict["menu_mod"],
        )

    @classmethod
    def default(cls) -> "PatcherConfiguration":
        return PatcherConfiguration(
            disable_hud_popup=True,
            menu_mod=True,
        )

    def bit_pack_format(self) -> Iterator[int]:
        yield 2
        yield 2

    def bit_pack_arguments(self) -> Iterator[int]:
        yield int(self.disable_hud_popup)
        yield int(self.menu_mod)

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder):
        disable_hud_popup, menu_mod = decoder.decode(2, 2)
        return cls(
            disable_hud_popup=bool(disable_hud_popup),
            menu_mod=bool(menu_mod),
        )
