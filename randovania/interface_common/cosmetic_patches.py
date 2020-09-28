import dataclasses

from randovania.interface_common.echoes_user_preferences import EchoesUserPreferences


@dataclasses.dataclass(frozen=True)
class CosmeticPatches:
    disable_hud_popup: bool = True
    speed_up_credits: bool = True
    open_map: bool = True
    pickup_markers: bool = True
    user_preferences: EchoesUserPreferences = dataclasses.field(default_factory=EchoesUserPreferences)

    @property
    def as_json(self) -> dict:
        return {
            "disable_hud_popup": self.disable_hud_popup,
            "speed_up_credits": self.speed_up_credits,
            "open_map": self.open_map,
            "pickup_markers": self.pickup_markers,
            "user_preferences": self.user_preferences.as_json,
        }

    @classmethod
    def from_json_dict(cls, json_dict: dict) -> "CosmeticPatches":
        return cls(
            disable_hud_popup=json_dict["disable_hud_popup"],
            speed_up_credits=json_dict["speed_up_credits"],
            open_map=json_dict["open_map"],
            pickup_markers=json_dict["pickup_markers"],
            user_preferences=(EchoesUserPreferences.from_json_dict(json_dict["user_preferences"])
                              if "user_preferences" in json_dict else EchoesUserPreferences())
        )

    @classmethod
    def default(cls) -> "CosmeticPatches":
        return cls()
