import dataclasses

from randovania.games.game import RandovaniaGame
from randovania.layout.base.base_configuration import BaseConfiguration


@dataclasses.dataclass(frozen=True)
class AM2RConfiguration(BaseConfiguration):
    energy_per_tank: int = dataclasses.field(metadata={"min": 1, "max": 1000, "precision": 1})
    # These fields aren't necessary for a new game: they're here to have example/test features
    #include_extra_pickups: bool

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.AM2R

    def active_layers(self) -> set[str]:
        result = super().active_layers()

        #if self.include_extra_pickups:
        #    result.add("extra_pickups")

        return result
