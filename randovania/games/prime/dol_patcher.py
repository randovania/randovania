from pathlib import Path
from typing import Dict

from randovania import get_data_path
from randovania.dol_patching.assembler import ppc
from randovania.dol_patching.dol_file import DolFile
from randovania.dol_patching.dol_version import find_version_for_dol
from randovania.game_description.echoes_game_specific import EchoesGameSpecific
from randovania.games.prime import echoes_dol_versions, all_prime_dol_patches, echoes_dol_patches
from randovania.games.prime.all_prime_dol_patches import BasePrimeDolVersion
from randovania.games.prime.echoes_dol_patches import EchoesDolVersion
from randovania.interface_common.echoes_user_preferences import EchoesUserPreferences

ALL_VERSIONS_PATCHES = echoes_dol_versions.ALL_VERSIONS


def align_to_32(value: int) -> int:
    return (value + 31) & ~31


def get_rel_load_patch(name: str):
    bin_path = get_data_path().joinpath("dols", name)
    bin_patch = bin_path.read_bytes()
    aligned_size = align_to_32(len(bin_patch))
    bin_patch += b"\x00" * (aligned_size - len(bin_patch))
    return bin_patch


def load_symbols(symbols: Dict[str, int], name: str):
    bin_map = get_data_path().joinpath("dols", name).read_text("utf-8")
    for line in bin_map.splitlines():
        symbol_line = line.strip().split(" ", 1)
        if len(symbol_line) == 2:
            symbols[symbol_line[1]] = int(symbol_line[0], 16)


def apply_patches(game_root: Path, game_specific: EchoesGameSpecific, user_preferences: EchoesUserPreferences,
                  default_items: dict, unvisited_room_names: bool, teleporter_sounds: bool):
    dol_file = DolFile(_get_dol_path(game_root))

    version = find_version_for_dol(dol_file, ALL_VERSIONS_PATCHES)
    if not isinstance(version, BasePrimeDolVersion):
        return

    dol_file.set_editable(True)
    load_symbols(dol_file.symbols, "prime2/v1.028.map")

    with dol_file:
        if dol_file.header.section_for_address(0x80002000) is None:
            dol_file.add_text_section(0x80002000, get_rel_load_patch("prime2/v1.028.bin"))

        dol_file.write_instructions(dol_file.resolve_symbol("PPCSetFpIEEEMode") + 4, [
            ppc.b("rel_loader_hook"),
        ])

        all_prime_dol_patches.apply_remote_execution_patch(version.string_display, dol_file)
        all_prime_dol_patches.apply_energy_tank_capacity_patch(version.health_capacity, game_specific, dol_file)
        all_prime_dol_patches.apply_reverse_energy_tank_heal_patch(version.sda2_base, version.dangerous_energy_tank,
                                                                   game_specific.dangerous_energy_tank,
                                                                   version.game, dol_file)

        if isinstance(version, EchoesDolVersion):
            echoes_dol_patches.apply_fixes(version, dol_file)
            echoes_dol_patches.apply_unvisited_room_names(version, dol_file, unvisited_room_names)
            echoes_dol_patches.apply_teleporter_sounds(version, dol_file, teleporter_sounds)

            echoes_dol_patches.apply_game_options_patch(version.game_options_constructor_address,
                                                        user_preferences, dol_file)
            echoes_dol_patches.apply_beam_cost_patch(version.beam_cost_addresses, game_specific, dol_file)
            echoes_dol_patches.apply_safe_zone_heal_patch(version.safe_zone, version.sda2_base, game_specific, dol_file)
            echoes_dol_patches.apply_starting_visor_patch(version.starting_beam_visor, default_items, dol_file)


def _get_dol_path(game_root: Path) -> Path:
    return game_root.joinpath("sys/main.dol")
