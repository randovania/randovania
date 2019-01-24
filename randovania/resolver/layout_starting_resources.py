from dataclasses import dataclass
from typing import Iterator

from randovania.bitpacking.bitpacking import BitPackValue, BitPackDecoder


@dataclass(frozen=True)
class LayoutStartingResources(BitPackValue):
    has_scan_visor: bool
    has_charge_beam: bool
    has_morph_ball: bool

    def bit_pack_format(self) -> Iterator[int]:
        yield from []

    def bit_pack_arguments(self) -> Iterator[int]:
        yield from []

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder):
        return cls()
