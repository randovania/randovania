from typing import Dict

from randovania.game_description.item.ammo import Ammo
from randovania.layout.ammo_state import AmmoState


class AmmoConfiguration:
    items_state: Dict[Ammo, AmmoState]
    is_beam_ammo_split: bool

    @property
    def as_json(self) -> dict:
        return {
            "items_state": {
                ammo.name: state.as_json
                for ammo, state in self.items_state.items()
            },
            "is_beam_ammo_split": self.is_beam_ammo_split,
        }
