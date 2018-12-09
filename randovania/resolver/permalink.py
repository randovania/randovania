from dataclasses import dataclass
from typing import Iterator

from randovania.bitpacking.bitpacking import BitPackDecoder, BitPackValue
from randovania.resolver.layout_configuration import LayoutConfiguration
from randovania.resolver.patcher_configuration import PatcherConfiguration

_PERMALINK_MAX_VERSION = 16
_PERMALINK_MAX_SEED = 2 ** 31


@dataclass(frozen=True)
class Permalink(BitPackValue):
    seed_number: int
    spoiler: bool
    patcher_configuration: PatcherConfiguration
    layout_configuration: LayoutConfiguration

    def __post_init__(self):
        if not (0 <= self.seed_number < _PERMALINK_MAX_SEED):
            raise ValueError("Invalid seed number: {}".format(self.seed_number))

    @classmethod
    def current_version(cls) -> int:
        # When this reaches _PERMALINK_MAX_VERSION, we need to change how we decode to avoid breaking version detection
        # for previous Randovania versions
        return 0

    def bit_pack_format(self) -> Iterator[int]:
        yield _PERMALINK_MAX_VERSION
        yield _PERMALINK_MAX_SEED
        yield 2
        yield from self.patcher_configuration.bit_pack_format()
        yield from self.layout_configuration.bit_pack_format()

    def bit_pack_arguments(self) -> Iterator[int]:
        yield self.current_version()
        yield self.seed_number
        yield int(self.spoiler)
        yield from self.patcher_configuration.bit_pack_arguments()
        yield from self.layout_configuration.bit_pack_arguments()

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder) -> "Permalink":
        version, seed, spoiler = decoder.decode(_PERMALINK_MAX_VERSION, _PERMALINK_MAX_SEED, 2)

        if version != cls.current_version():
            raise Exception("Unsupported Permalink version.")

        patcher_configuration = PatcherConfiguration.bit_pack_unpack(decoder)
        layout_configuration = LayoutConfiguration.bit_pack_unpack(decoder)
        return Permalink(
            seed,
            bool(spoiler),
            patcher_configuration,
            layout_configuration
        )
