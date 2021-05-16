import dataclasses

from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.interface_common.echoes_user_preferences import EchoesUserPreferences


@dataclasses.dataclass(frozen=True)
class CosmeticPatches(JsonDataclass):
    disable_hud_popup: bool = True
    speed_up_credits: bool = True
    open_map: bool = True
    unvisited_room_names: bool = True
    pickup_markers: bool = True
    teleporter_sounds: bool = True
    user_preferences: EchoesUserPreferences = dataclasses.field(default_factory=EchoesUserPreferences)

    @classmethod
    def default(cls) -> "CosmeticPatches":
        return cls()
