from __future__ import annotations

from typing import TYPE_CHECKING, override

from randovania.exporter.patch_data_factory import PatchDataFactory
from randovania.game.game_enum import RandovaniaGame
from randovania.games.prime2_dev.exporter.hint_namer import EchoesHintNamer
from randovania.games.prime2_dev.layout import EchoesConfiguration, EchoesCosmeticPatches

if TYPE_CHECKING:
    from randovania.exporter.hints.hint_namer import HintNamer
    from randovania.exporter.patch_data_factory import PatcherDataMeta


class EchoesPatchDataFactory(PatchDataFactory[EchoesConfiguration, EchoesCosmeticPatches]):
    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.METROID_PRIME_ECHOES_DEV

    def create_game_specific_data(self, randovania_meta: PatcherDataMeta) -> dict:
        return {}

    @override
    @classmethod
    def hint_namer_type(cls) -> type[HintNamer]:
        return EchoesHintNamer
