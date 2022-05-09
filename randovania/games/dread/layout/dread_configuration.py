import dataclasses

from randovania.games.game import RandovaniaGame
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.lib.teleporters import TeleporterConfiguration


@dataclasses.dataclass(frozen=True)
class DreadConfiguration(BaseConfiguration):
    elevators: TeleporterConfiguration
    energy_per_tank: int = dataclasses.field(metadata={"min": 1, "max": 1000, "precision": 1})
    immediate_energy_parts: bool
    hanubia_shortcut_no_grapple: bool
    hanubia_easier_path_to_itorash: bool
    extra_pickups_for_bosses: bool
    x_starts_released: bool

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_DREAD

    def active_layers(self) -> set[str]:
        result = super().active_layers()
        if self.extra_pickups_for_bosses:
            result.add("extra_pickup_drops")
        return result
