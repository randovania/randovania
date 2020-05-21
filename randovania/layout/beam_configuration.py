import dataclasses
from typing import Tuple

from randovania.bitpacking.bitpacking import BitPackValue, BitPackDataClass
from randovania.game_description.echoes_game_specific import EchoesBeamConfiguration
from randovania.game_description.resources.resource_database import ResourceDatabase


@dataclasses.dataclass(frozen=True)
class BeamAmmoConfiguration(BitPackDataClass):
    item_index: int = dataclasses.field(metadata={"min": 0, "max": 108})
    ammo_a: int = dataclasses.field(metadata={"min": -1, "max": 108})
    ammo_b: int = dataclasses.field(metadata={"min": -1, "max": 108})
    uncharged_cost: int = dataclasses.field(metadata={"min": 0, "max": 250, "if_different": 1})
    charged_cost: int = dataclasses.field(metadata={"min": 0, "max": 250, "if_different": 5})
    combo_missile_cost: int = dataclasses.field(metadata={"min": 1, "max": 250, "if_different": 5})
    combo_ammo_cost: int = dataclasses.field(metadata={"min": 0, "max": 250, "if_different": 30})

    def create_game_specific(self, resource_database: ResourceDatabase) -> EchoesBeamConfiguration:
        return EchoesBeamConfiguration(
            item=resource_database.get_item(self.item_index),
            ammo_a=resource_database.get_item(self.ammo_a) if self.ammo_a >= 0 else None,
            ammo_b=resource_database.get_item(self.ammo_b) if self.ammo_b >= 0 else None,
            uncharged_cost=self.uncharged_cost,
            charged_cost=self.charged_cost,
            combo_missile_cost=self.combo_missile_cost,
            combo_ammo_cost=self.combo_ammo_cost,
        )

    @property
    def as_json(self) -> dict:
        return {
            field.name: getattr(self, field.name)
            for field in dataclasses.fields(self)
        }

    @classmethod
    def from_json(cls, json_dict: dict) -> "BeamAmmoConfiguration":
        kwargs = {
            field.name: json_dict[field.name]
            for field in dataclasses.fields(cls)
        }
        return cls(**kwargs)


@dataclasses.dataclass(frozen=True)
class BeamConfiguration(BitPackDataClass):
    power: BeamAmmoConfiguration
    dark: BeamAmmoConfiguration
    light: BeamAmmoConfiguration
    annihilator: BeamAmmoConfiguration

    @property
    def as_json(self) -> dict:
        return {
            field.name: getattr(self, field.name).as_json
            for field in dataclasses.fields(self)
        }

    @classmethod
    def from_json(cls, json_dict: dict) -> "BeamConfiguration":
        kwargs = {
            field.name: field.type.from_json(json_dict[field.name])
            for field in dataclasses.fields(cls)
        }
        return cls(**kwargs)

    def create_game_specific(self, resource_database: ResourceDatabase) -> Tuple[EchoesBeamConfiguration, ...]:
        return (
            self.power.create_game_specific(resource_database),
            self.dark.create_game_specific(resource_database),
            self.light.create_game_specific(resource_database),
            self.annihilator.create_game_specific(resource_database),
        )
