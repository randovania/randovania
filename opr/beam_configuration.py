import dataclasses


@dataclasses.dataclass(frozen=True)
class BeamAmmoConfiguration:
    item_index: int = dataclasses.field(metadata={"min": 0, "max": 108})
    ammo_a: int = dataclasses.field(metadata={"min": -1, "max": 108})
    ammo_b: int = dataclasses.field(metadata={"min": -1, "max": 108})
    uncharged_cost: int = dataclasses.field(metadata={"min": 0, "max": 250, "if_different": 1})
    charged_cost: int = dataclasses.field(metadata={"min": 0, "max": 250, "if_different": 5})
    combo_missile_cost: int = dataclasses.field(metadata={"min": 1, "max": 250, "if_different": 5})
    combo_ammo_cost: int = dataclasses.field(metadata={"min": 0, "max": 250, "if_different": 30})

    @classmethod
    def from_json(cls, data: dict) -> "BeamAmmoConfiguration":
        return cls(
            item_index=data["item_index"],
            ammo_a=data["ammo_a"],
            ammo_b=data["ammo_b"],
            uncharged_cost=data["uncharged_cost"],
            charged_cost=data["charged_cost"],
            combo_missile_cost=data["combo_missile_cost"],
            combo_ammo_cost=data["combo_ammo_cost"],
        )
