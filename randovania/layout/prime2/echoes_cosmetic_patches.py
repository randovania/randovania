import dataclasses

from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.games.game import RandovaniaGame
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches
from randovania.layout.prime2.echoes_user_preferences import EchoesUserPreferences


@dataclasses.dataclass(frozen=True)
class EchoesCosmeticPatches(BaseCosmeticPatches):
    disable_hud_popup: bool = True
    speed_up_credits: bool = True
    open_map: bool = True
    unvisited_room_names: bool = True
    pickup_markers: bool = True
    teleporter_sounds: bool = True
    user_preferences: EchoesUserPreferences = dataclasses.field(default_factory=EchoesUserPreferences)

    @classmethod
    def default(cls) -> "EchoesCosmeticPatches":
        return cls()

    @classmethod
    def game(cls):
        return RandovaniaGame.METROID_PRIME_ECHOES
