from dataclasses import dataclass


@dataclass(frozen=True)
class CosmeticPatches:
    disable_hud_popup: bool = True
    speed_up_credits: bool = True
    open_map: bool = True
    pickup_markers: bool = True

    @property
    def as_json(self) -> dict:
        return {
            "disable_hud_popup": self.disable_hud_popup,
            "speed_up_credits": self.speed_up_credits,
            "open_map": self.open_map,
            "pickup_markers": self.pickup_markers,
        }

    @classmethod
    def from_json_dict(cls, json_dict: dict) -> "CosmeticPatches":
        return cls(
            disable_hud_popup=json_dict["disable_hud_popup"],
            speed_up_credits=json_dict["speed_up_credits"],
            open_map=json_dict["open_map"],
            pickup_markers=json_dict["pickup_markers"],
        )

    @classmethod
    def default(cls) -> "CosmeticPatches":
        return cls()
