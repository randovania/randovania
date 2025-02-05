from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.exporter.hints.hint_exporter import HintExporter

if TYPE_CHECKING:
    from randovania.game_description.hint import Hint


class CSHintExporter(HintExporter):
    def create_message_for_hint(self, hint: Hint, with_color: bool) -> str:
        starts = ["I hear that", "Rumour has it,", "They say"]
        mids = ["can be found", "is", "is hidden"]

        unformatted_message = super().create_message_for_hint(hint, with_color)

        return unformatted_message.format(
            start=self.rng.choice(starts),
            mid=self.rng.choice(mids),
        )
