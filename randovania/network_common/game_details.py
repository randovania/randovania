from __future__ import annotations

import dataclasses

import typing_extensions

from randovania.bitpacking.json_dataclass import JsonDataclass

if typing_extensions.TYPE_CHECKING:
    from randovania.layout.layout_description import LayoutDescription


@dataclasses.dataclass(frozen=True)
class GameDetails(JsonDataclass):
    seed_hash: str
    word_hash: str
    spoiler: bool

    @classmethod
    def from_layout(cls, layout: LayoutDescription) -> typing_extensions.Self:
        return cls(
            spoiler=layout.has_spoiler,
            word_hash=layout.shareable_word_hash,
            seed_hash=layout.shareable_hash,
        )
