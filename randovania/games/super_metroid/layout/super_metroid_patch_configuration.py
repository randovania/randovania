import dataclasses
from typing import Iterator
from enum import Enum

from randovania.bitpacking.bitpacking import BitPackDataclass
from randovania.bitpacking.json_dataclass import JsonDataclass

class MusicMode(Enum):
    VANILLA = 0
    RANDOMIZED = 1
    OFF = 2

@dataclasses.dataclass(frozen=True)
class SuperPatchConfiguration(BitPackDataclass, JsonDataclass):
    colorblind_mode: bool = False
    instant_g4: bool = True
    max_ammo_display: bool = True
    aim_with_any_button: bool = True
    fast_doors_and_elevators: bool = True
    backup_saves: bool = True
    better_decompression: bool = True
    skip_intro: bool = True
    mother_brain_cutscene_edits: bool = True
    no_demo: bool = True
    dachora_pit: bool = True
    early_supers_bridge: bool = True
    pre_hi_jump: bool = True
    moat: bool = True
    pre_spazer: bool = True
    red_tower: bool = True
    nova_boost_platform: bool = True
    respin: bool = True
    refill_before_save: bool = False
    cant_use_supers_on_red_doors: bool = False
    cheap_charge: bool = False
    speedkeep: bool = False
    infinite_space_jump: bool = False
    nerfed_rainbow_beam: bool = False
    fix_spacetime: bool = True
    fix_heat_echoes: bool = True
    fix_screw_attack_menu: bool = True
    no_gt_code: bool = True
    music: MusicMode = MusicMode.VANILLA