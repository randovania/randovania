from dataclasses import dataclass

from randovania.bitpacking.bitpacking import BitPackDataClass


@dataclass(frozen=True)
class ShuffledItems(BitPackDataClass):
    sky_temple_keys: bool
    dark_temple_keys: bool
    missile_launcher: bool
    morph_ball_bombs: bool
    space_jump: bool

    scan_visor: bool
    morph_ball: bool
    charge_beam: bool

    @classmethod
    def default(cls) -> "ShuffledItems":
        return cls(
            sky_temple_keys=True,
            dark_temple_keys=True,
            missile_launcher=True,
            morph_ball_bombs=True,
            space_jump=True,
            scan_visor=False,
            morph_ball=False,
            charge_beam=False,
        )

    @property
    def as_json(self) -> dict:
        return {
            "sky_temple_keys": self.sky_temple_keys,
            "dark_temple_keys": self.dark_temple_keys,
            "missile_launcher": self.missile_launcher,
            "morph_ball_bombs": self.morph_ball_bombs,
            "space_jump": self.space_jump,
            "scan_visor": self.scan_visor,
            "morph_ball": self.morph_ball,
            "charge_beam": self.charge_beam,
        }

    @classmethod
    def from_json(cls, value: dict) -> "ShuffledItems":
        return cls(
            sky_temple_keys=value["sky_temple_keys"],
            dark_temple_keys=value["dark_temple_keys"],
            missile_launcher=value["missile_launcher"],
            morph_ball_bombs=value["morph_ball_bombs"],
            space_jump=value["space_jump"],
            scan_visor=value["scan_visor"],
            morph_ball=value["morph_ball"],
            charge_beam=value["charge_beam"],
        )
