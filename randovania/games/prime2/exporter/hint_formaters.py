from typing import Callable

from randovania.exporter.hints.hint_formatters import LocationFormatter
from randovania.exporter.hints.pickup_hint import PickupHint
from randovania.game_description.hint import Hint
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame


class GuardianFormatter(LocationFormatter):
    _GUARDIAN_NAMES = {
        PickupIndex(43): "Amorbis",
        PickupIndex(79): "Chykka",
        PickupIndex(115): "Quadraxis",
    }

    def __init__(self, colorizer: Callable[[str, bool], str]):
        self.colorizer = colorizer

    def format(self, game: RandovaniaGame, pick_hint: PickupHint, hint: Hint, with_color: bool) -> str:
        guardian = self._GUARDIAN_NAMES[hint.target]
        return f"{self.colorizer(guardian, with_color)} is guarding {pick_hint.determiner}{pick_hint.pickup_name}."
