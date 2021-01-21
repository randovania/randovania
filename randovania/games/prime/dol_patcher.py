from pathlib import Path

from randovania.dol_patching.dol_file import DolFile
from randovania.dol_patching.dol_version import find_version_for_dol
from randovania.game_description.echoes_game_specific import EchoesGameSpecific
from randovania.games.prime import echoes_dol_versions, all_prime_dol_patches, echoes_dol_patches
from randovania.games.prime.all_prime_dol_patches import BasePrimeDolVersion
from randovania.games.prime.echoes_dol_patches import EchoesDolVersion
from randovania.interface_common.echoes_user_preferences import EchoesUserPreferences

ALL_VERSIONS_PATCHES = echoes_dol_versions.ALL_VERSIONS


def apply_patches(game_root: Path, game_specific: EchoesGameSpecific, user_preferences: EchoesUserPreferences,
                  default_items: dict):
    dol_file = DolFile(_get_dol_path(game_root))

    version = find_version_for_dol(dol_file, ALL_VERSIONS_PATCHES)
    if not isinstance(version, BasePrimeDolVersion):
        return

    dol_file.set_editable(True)
    with dol_file:
        all_prime_dol_patches.apply_remote_execution_patch(version.string_display, dol_file)
        all_prime_dol_patches.apply_energy_tank_capacity_patch(version.health_capacity, game_specific, dol_file)
        all_prime_dol_patches.apply_reverse_energy_tank_heal_patch(version.sda2_base, version.dangerous_energy_tank,
                                                                   game_specific.dangerous_energy_tank,
                                                                   version.game, dol_file)

        if isinstance(version, EchoesDolVersion):
            echoes_dol_patches.apply_game_options_patch(version.game_options_constructor_address,
                                                        user_preferences, dol_file)
            echoes_dol_patches.apply_beam_cost_patch(version.beam_cost_addresses, game_specific, dol_file)
            echoes_dol_patches.apply_safe_zone_heal_patch(version.safe_zone, version.sda2_base, game_specific, dol_file)
            echoes_dol_patches.apply_starting_visor_patch(version.starting_beam_visor, default_items, dol_file)


def _get_dol_path(game_root: Path) -> Path:
    return game_root.joinpath("sys/main.dol")
