import dataclasses
import uuid

from ppc_asm.dol_file import DolFile

from opr import all_prime_dol_patches, echoes_dol_patches, echoes_dol_versions, dol_version
from opr.beam_configuration import BeamAmmoConfiguration
from opr.echoes_dol_patches import EchoesDolVersion
from opr.echoes_user_preferences import OprEchoesUserPreferences


@dataclasses.dataclass(frozen=True)
class EchoesDolPatchesData:
    world_uuid: uuid.UUID
    energy_per_tank: int
    beam_configurations: list[BeamAmmoConfiguration]
    safe_zone_heal_per_second: float
    user_preferences: OprEchoesUserPreferences
    default_items: dict
    unvisited_room_names: bool
    teleporter_sounds: bool
    dangerous_energy_tank: bool

    @classmethod
    def from_json(cls, data: dict):
        return cls(
            world_uuid=uuid.UUID(data["world_uuid"]),
            energy_per_tank=data["energy_per_tank"],
            beam_configurations=[BeamAmmoConfiguration.from_json(it) for it in data["beam_configurations"]],
            safe_zone_heal_per_second=data["safe_zone_heal_per_second"],
            user_preferences=OprEchoesUserPreferences.from_json(data["user_preferences"]),
            default_items=data["default_items"],
            unvisited_room_names=data["unvisited_room_names"],
            teleporter_sounds=data["teleporter_sounds"],
            dangerous_energy_tank=data["dangerous_energy_tank"],
        )


def apply_patches(dol_file: DolFile, patches_data: EchoesDolPatchesData):
    version = dol_version.find_version_for_dol(dol_file, echoes_dol_versions.ALL_VERSIONS)
    assert isinstance(version, EchoesDolVersion)

    dol_file.set_editable(True)
    with dol_file:
        all_prime_dol_patches.apply_build_info_patch(dol_file, patches_data.world_uuid, version)
        all_prime_dol_patches.apply_remote_execution_patch(version.game, version.string_display, dol_file)
        all_prime_dol_patches.apply_energy_tank_capacity_patch(version.health_capacity, patches_data.energy_per_tank,
                                                               dol_file)
        all_prime_dol_patches.apply_reverse_energy_tank_heal_patch(version.sda2_base, version.dangerous_energy_tank,
                                                                   patches_data.dangerous_energy_tank,
                                                                   version.game, dol_file)

        echoes_dol_patches.apply_fixes(version, dol_file)
        echoes_dol_patches.change_powerup_should_persist(
            version, dol_file,
            ["Double Damage", "Unlimited Missiles", "Unlimited Beam Ammo"]
        )

        echoes_dol_patches.apply_unvisited_room_names(version, dol_file, patches_data.unvisited_room_names)
        echoes_dol_patches.apply_teleporter_sounds(version, dol_file, patches_data.teleporter_sounds)

        echoes_dol_patches.apply_game_options_patch(version.game_options_constructor_address,
                                                    patches_data.user_preferences, dol_file)
        echoes_dol_patches.apply_beam_cost_patch(version.beam_cost_addresses, patches_data.beam_configurations,
                                                 dol_file)
        echoes_dol_patches.apply_safe_zone_heal_patch(version.safe_zone, version.sda2_base,
                                                      patches_data.safe_zone_heal_per_second, dol_file)
        echoes_dol_patches.apply_starting_visor_patch(version.starting_beam_visor, patches_data.default_items,
                                                      dol_file)
        echoes_dol_patches.apply_map_door_changes(version.map_door_types, dol_file)
