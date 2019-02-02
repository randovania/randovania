from dataclasses import dataclass


@dataclass(frozen=True)
class CosmeticPatches:
    disable_hud_popup: bool
    speed_up_credits: bool

    @property
    def as_json(self) -> dict:
        return {
            "disable_hud_popup": self.disable_hud_popup,
            "speed_up_credits": self.speed_up_credits,
        }

    @classmethod
    def from_json_dict(cls, json_dict: dict) -> "CosmeticPatches":
        return cls(
            disable_hud_popup=json_dict["disable_hud_popup"],
            speed_up_credits=json_dict["speed_up_credits"],
        )

    @classmethod
    def default(cls) -> "CosmeticPatches":
        return cls(
            disable_hud_popup=True,
            speed_up_credits=True,
        )
