from dataclasses import dataclass
from typing import Iterator

from randovania.bitpacking.bitpacking import BitPackDataClass, BitPackDecoder, BitPackValue
from randovania.resolver.layout_configuration import LayoutEnabledFlag, LayoutConfiguration


@dataclass(frozen=True)
class PermalinkConfiguration(BitPackDataClass):
    spoiler: LayoutEnabledFlag
    disable_hud_popup: LayoutEnabledFlag
    menu_mod: LayoutEnabledFlag

    @property
    def as_json(self) -> dict:
        return {
            "spoiler": self.spoiler.value,
            "disable_hud_popup": self.disable_hud_popup.value,
            "menu_mod": self.menu_mod.value,
        }

    @classmethod
    def from_json_dict(cls, json_dict: dict) -> "PermalinkConfiguration":
        return PermalinkConfiguration(
            spoiler=LayoutEnabledFlag(json_dict["spoiler"]),
            disable_hud_popup=LayoutEnabledFlag(json_dict["disable_hud_popup"]),
            menu_mod=LayoutEnabledFlag(json_dict["menu_mod"]),
        )


_PERMALINK_MAX_VERSION = 16
_PERMALINK_MAX_SEED = 2 ** 31


@dataclass(frozen=True)
class Permalink(BitPackValue):
    seed_number: int
    permalink_configuration: PermalinkConfiguration
    layout_configuration: LayoutConfiguration

    @classmethod
    def current_version(cls) -> int:
        # When this reaches _PERMALINK_MAX_VERSION, we need to change how we decode to avoid breaking version detection
        # for previous Randovania versions
        return 0

    def bit_pack_format(self) -> Iterator[int]:
        yield _PERMALINK_MAX_VERSION
        yield _PERMALINK_MAX_SEED
        yield from self.permalink_configuration.bit_pack_format()
        yield from self.layout_configuration.bit_pack_format()

    def bit_pack_arguments(self) -> Iterator[int]:
        yield self.current_version()
        yield self.seed_number
        yield from self.permalink_configuration.bit_pack_arguments()
        yield from self.layout_configuration.bit_pack_arguments()

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder) -> "Permalink":
        version, seed = decoder.decode(_PERMALINK_MAX_VERSION, _PERMALINK_MAX_SEED)

        if version != cls.current_version():
            raise Exception("Unsupported Permalink version.")

        permalink_configuration = PermalinkConfiguration.bit_pack_unpack(decoder)
        layout_configuration = LayoutConfiguration.bit_pack_unpack(decoder)
        return Permalink(
            seed,
            permalink_configuration,
            layout_configuration
        )
