from dataclasses import dataclass
from typing import Dict

from randovania.game_description.item.ammo import Ammo
from randovania.game_description.item.item_database import ItemDatabase
from randovania.layout.ammo_state import AmmoState


@dataclass(frozen=True)
class AmmoConfiguration:
    items_state: Dict[Ammo, AmmoState]

    @property
    def as_json(self) -> dict:
        return {
            "items_state": {
                ammo.name: state.as_json
                for ammo, state in self.items_state.items()
            },
        }

    @classmethod
    def from_json(cls, value: dict, item_database: ItemDatabase) -> "AmmoConfiguration":
        return cls(
            items_state={
                item_database.ammo[name]: AmmoState.from_json(state)
                for name, state in value["items_state"].items()
            },
        )
