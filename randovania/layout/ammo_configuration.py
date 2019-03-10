import copy
from dataclasses import dataclass
from typing import Dict

from randovania.game_description.item.ammo import Ammo
from randovania.game_description.item.item_database import ItemDatabase
from randovania.layout.ammo_state import AmmoState


@dataclass(frozen=True)
class AmmoConfiguration:
    maximum_ammo: Dict[int, int]
    items_state: Dict[Ammo, AmmoState]

    @property
    def as_json(self) -> dict:
        return {
            "maximum_ammo": {
                str(ammo_item): maximum
                for ammo_item, maximum in self.maximum_ammo.items()
            },
            "items_state": {
                ammo.name: state.as_json
                for ammo, state in self.items_state.items()
            },
        }

    @classmethod
    def from_json(cls, value: dict, item_database: ItemDatabase) -> "AmmoConfiguration":
        return cls(
            maximum_ammo={
                int(ammo_item): maximum
                for ammo_item, maximum in value["maximum_ammo"].items()
            },
            items_state={
                item_database.ammo[name]: AmmoState.from_json(state)
                for name, state in value["items_state"].items()
            },
        )

    def replace_maximum_for_item(self, item: int, maximum: int) -> "AmmoConfiguration":
        return AmmoConfiguration(
            maximum_ammo={
                key: maximum if key == item else value
                for key, value in self.maximum_ammo.items()
            },
            items_state=copy.copy(self.items_state),
        )

    def replace_state_for_ammo(self, ammo: Ammo, state: AmmoState) -> "AmmoConfiguration":
        return AmmoConfiguration(
            maximum_ammo=copy.copy(self.maximum_ammo),
            items_state={
                key: state if key == ammo else value
                for key, value in self.items_state.items()
            }
        )
