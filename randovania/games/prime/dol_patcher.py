import dataclasses
from pathlib import Path

from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.dol_patching.dol_file import DolFile
from randovania.dol_patching.dol_version import find_version_for_dol
from randovania.games.prime import echoes_dol_versions, all_prime_dol_patches, echoes_dol_patches, prime1_dol_versions
from randovania.games.prime.all_prime_dol_patches import BasePrimeDolVersion
from randovania.games.prime.echoes_dol_patches import EchoesDolVersion, BeamConfiguration
from randovania.interface_common.echoes_user_preferences import EchoesUserPreferences

ALL_VERSIONS_PATCHES = echoes_dol_versions.ALL_VERSIONS + prime1_dol_versions.ALL_VERSIONS


@dataclasses.dataclass(frozen=True)
class DolPatchesData(JsonDataclass):
    energy_per_tank: int
    beam_configuration: BeamConfiguration
    safe_zone_heal_per_second: float
    user_preferences: EchoesUserPreferences
    default_items: dict
    unvisited_room_names: bool
    teleporter_sounds: bool
    dangerous_energy_tank: bool


def apply_patches(game_root: Path, patches_data: DolPatchesData):
    dol_file = DolFile(_get_dol_path(game_root))

    version = find_version_for_dol(dol_file, ALL_VERSIONS_PATCHES)
    if not isinstance(version, BasePrimeDolVersion):
        return

    dol_file.set_editable(True)
    with dol_file:
        all_prime_dol_patches.apply_remote_execution_patch(version.string_display, dol_file)
        all_prime_dol_patches.apply_energy_tank_capacity_patch(version.health_capacity, patches_data.energy_per_tank,
                                                               dol_file)
        all_prime_dol_patches.apply_reverse_energy_tank_heal_patch(version.sda2_base, version.dangerous_energy_tank,
                                                                   patches_data.dangerous_energy_tank,
                                                                   version.game, dol_file)

        if isinstance(version, EchoesDolVersion):
            echoes_dol_patches.apply_fixes(version, dol_file)
            echoes_dol_patches.apply_unvisited_room_names(version, dol_file, patches_data.unvisited_room_names)
            echoes_dol_patches.apply_teleporter_sounds(version, dol_file, patches_data.teleporter_sounds)

            echoes_dol_patches.apply_game_options_patch(version.game_options_constructor_address,
                                                        patches_data.user_preferences, dol_file)
            echoes_dol_patches.apply_beam_cost_patch(version.beam_cost_addresses, patches_data.beam_configuration,
                                                     dol_file)
            echoes_dol_patches.apply_safe_zone_heal_patch(version.safe_zone, version.sda2_base,
                                                          patches_data.safe_zone_heal_per_second, dol_file)
            echoes_dol_patches.apply_starting_visor_patch(version.starting_beam_visor, patches_data.default_items,
                                                          dol_file)


def _get_dol_path(game_root: Path) -> Path:
    return game_root.joinpath("sys/main.dol")
