import dataclasses

from randovania.bitpacking.bitpacking import BitPackDataclass
from randovania.bitpacking.json_dataclass import JsonDataclass


@dataclasses.dataclass(frozen=True)
class SuperPatchConfiguration(BitPackDataclass, JsonDataclass):
    instant_g4: bool
    fast_doors_and_elevators: bool
    backup_saves: bool
    better_decompression: bool
    skip_intro: bool
    mother_brain_cutscene_edits: bool
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
