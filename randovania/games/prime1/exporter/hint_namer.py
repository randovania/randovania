from __future__ import annotations

from typing import override

from randovania.games.common.prime_family.exporter.hint_namer import PrimeFamilyHintNamer


class PrimeHintNamer(PrimeFamilyHintNamer):
    @override
    @property
    def color_joke(self) -> str:
        return "#45F731"

    @override
    @property
    def color_item(self) -> str:
        return "#c300ff"

    @override
    @property
    def color_world(self) -> str:
        return "#d4cc33"

    @override
    @property
    def color_location(self) -> str:
        return "#89a1ff"
