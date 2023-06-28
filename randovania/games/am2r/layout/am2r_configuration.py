import dataclasses

from randovania.bitpacking.bitpacking import BitPackDataclass
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.games.game import RandovaniaGame
from randovania.layout.base.base_configuration import BaseConfiguration


@dataclasses.dataclass(frozen=True)
class AM2RArtifactConfig(BitPackDataclass, JsonDataclass):
    prefer_metroids: bool
    prefer_bosses: bool
    required_artifacts: int = dataclasses.field(metadata={"min": 0, "max": 46, "precision": 1})

@dataclasses.dataclass(frozen=True)
class AM2RConfiguration(BaseConfiguration):
    energy_per_tank: int = dataclasses.field(metadata={"min": 1, "max": 1000, "precision": 1})
    # TODO: add option for metroids and bosses to spawn pickups!
    #include_metroid_pickups: bool
    #include_boss_pickups: bool
    # TODO: ability to go to credits sooner?
    septogg_helpers: bool
    change_level_design: bool   # TODO: requires changes in DB!
    skip_cutscenes: bool        # TODO: requires changes in DB!
    respawn_bomb_blocks: bool   # TODO: requires changes in DB!
    artifacts: AM2RArtifactConfig
    # TODO: warp to start


    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.AM2R

    def active_layers(self) -> set[str]:
        result = super().active_layers()

        #if self.include_extra_pickups:
        #    result.add("extra_pickups")

        return result
