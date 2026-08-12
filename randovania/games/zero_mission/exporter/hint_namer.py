from __future__ import annotations

from typing import TYPE_CHECKING, override

from randovania.exporter.hints.basic_hint_formatters import basic_hint_formatters
from randovania.exporter.hints.hint_namer import HintNamer

if TYPE_CHECKING:
    from randovania.game_description.game_patches import GamePatches
    from randovania.interface_common.worlds_configuration import WorldsConfiguration


class MZMHintNamer(HintNamer[None]):
    def __init__(self, all_patches: list[GamePatches], worlds_config: WorldsConfiguration):
        super().__init__(all_patches, worlds_config)

        patches = all_patches[worlds_config.world_index]
        location_hint_template = "{determiner.title}{pickup} can be found in {node}."

        self.location_formatters = basic_hint_formatters(
            self,
            location_hint_template,
            patches,
            lambda msg, with_color: self.colorize_text(self.color_location, msg, with_color),
            worlds_config,
        )

    @override
    @property
    def color_default(self) -> None:
        return None
