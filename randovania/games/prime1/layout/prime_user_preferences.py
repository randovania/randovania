import dataclasses
from enum import IntEnum

from randovania.bitpacking.json_dataclass import JsonDataclass


def _int_field(default: int, min_value: int, max_value: int, display_as_percentage: bool = True):
    return dataclasses.field(default=default, metadata={"min": min_value, "max": max_value,
                                                        "display_as_percentage": display_as_percentage})


class SoundMode(IntEnum):
    MONO = 0
    STEREO = 1
    SURROUND = 2


@dataclasses.dataclass(frozen=True)
class PrimeUserPreferences(JsonDataclass):
    sound_mode: SoundMode = SoundMode.STEREO
    screen_brightness: int = _int_field(5, 2, 8, True)
    screen_x_offset: int = _int_field(0, -30, 30, False)
    screen_y_offset: int = _int_field(0, -30, 30, False)
    screen_stretch: int = _int_field(0, -10, 10, False)
    sfx_volume: int = _int_field(127, 0, 127, True)
    music_volume: int = _int_field(127, 0, 127, True)
    hud_alpha: int = _int_field(255, 0, 255, True)
    helmet_alpha: int = _int_field(255, 0, 255, True)
    hud_lag: bool = True
    invert_y_axis: bool = False
    rumble: bool = True
    swap_beam_controls: bool = False

    def __post_init__(self):
        for field in dataclasses.fields(self):
            value = getattr(self, field.name)
            if "min" in field.metadata and value < field.metadata["min"]:
                raise ValueError(f'Value {value} for field "{field.name}" is less than minimum {field.metadata["min"]}')
            if "max" in field.metadata and value > field.metadata["max"]:
                raise ValueError(f'Value {value} for field "{field.name}" is less than maximum {field.metadata["max"]}')
