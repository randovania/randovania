import dataclasses
from enum import Enum

from randovania.bitpacking.json_dataclass import JsonDataclass


def _int_field(default: int, min_value: int, max_value: int, display_as_percentage: bool = True):
    return dataclasses.field(default=default, metadata={"min": min_value, "max": max_value,
                                                        "display_as_percentage": display_as_percentage})


class SoundMode(Enum):
    MONO = 0
    STEREO = 1
    SURROUND = 2


@dataclasses.dataclass(frozen=True)
class EchoesUserPreferences(JsonDataclass):
    sound_mode: SoundMode = SoundMode.STEREO
    screen_brightness: int = _int_field(4, 0, 8)
    screen_x_offset: int = _int_field(0, -0x1e, 0x1f, False)
    screen_y_offset: int = _int_field(0, -0x1e, 0x1f, False)
    screen_stretch: int = _int_field(0, -10, 10, False)
    sfx_volume: int = _int_field(0x69, 0x00, 0x69)
    music_volume: int = _int_field(0x4f, 0x00, 0x69)
    hud_alpha: int = _int_field(0xff, 0x00, 0xff)
    helmet_alpha: int = _int_field(0xff, 0x00, 0xff)
    hud_lag: bool = True
    invert_y_axis: bool = False
    rumble: bool = True
    hint_system: bool = False

    def __post_init__(self):
        for field in dataclasses.fields(self):
            value = getattr(self, field.name)
            if "min" in field.metadata and value < field.metadata["min"]:
                raise ValueError(f'Value {value} for field "{field.name}" is less than minimum {field.metadata["min"]}')
            if "max" in field.metadata and value > field.metadata["max"]:
                raise ValueError(f'Value {value} for field "{field.name}" is less than maximum {field.metadata["max"]}')
