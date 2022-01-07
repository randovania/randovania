import dataclasses
from typing import Iterator
from enum import Enum

from randovania.bitpacking.bitpacking import BitPackDataclass, BitPackEnum
from randovania.bitpacking.json_dataclass import JsonDataclass


class MusicMode(BitPackEnum, Enum):
    VANILLA = "vanilla_music"
    RANDOMIZED = "random_music"
    OFF = "no_music"


@dataclasses.dataclass(frozen=True)
class SuperPatchConfiguration(BitPackDataclass, JsonDataclass):
    music: MusicMode
    colorblind_mode: bool
    instant_g4: bool
    max_ammo_display: bool
    aim_with_any_button: bool
    fast_doors_and_elevators: bool
    backup_saves: bool
    better_decompression: bool
    skip_intro: bool
    mother_brain_cutscene_edits: bool
    no_demo: bool
    dachora_pit: bool
    early_supers_bridge: bool
    pre_hi_jump: bool
    moat: bool
    pre_spazer: bool
    red_tower: bool
    nova_boost_platform: bool
    respin: bool
    refill_before_save: bool
    cant_use_supers_on_red_doors: bool
    cheap_charge: bool
    speedkeep: bool
    infinite_space_jump: bool
    nerfed_rainbow_beam: bool
    fix_spacetime: bool
    fix_heat_echoes: bool
    fix_screw_attack_menu: bool
    no_gt_code: bool
