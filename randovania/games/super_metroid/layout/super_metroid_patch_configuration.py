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
    rebindable_aim: bool = True
    faster_doors_and_elevators: bool = True
    backup_saves: bool = True
    better_decompression: bool = True
    skip_intro: bool = True
    mb_cutscene_tweaks: bool = True
    no_demo: bool = True
    dachora_pit: bool = True
    early_supers: bool = True
    pre_hi_jump: bool = True
    moat: bool = True
    pre_spazer: bool = True
    red_tower: bool = True
    nova_boost: bool = True
    respin: bool = True
    saves_refill_energy: bool = False
    cant_use_supers_on_red_doors: bool = False
    cheap_charge: bool = False
    speedkeep: bool = False
    isj: bool = False
    mb_rainbow_beam_nerf: bool = False
    fix_spacetime: bool = True
    fix_heat_echoes: bool = True
    fix_screw_attack_menu: bool = True
    no_gt_code: bool = True
    music: MusicMode = MusicMode.VANILLA