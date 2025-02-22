from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.lib import json_lib, migration_lib

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

_FIRST_VERSION_IN_SUBFOLDER = 18


def _only_new_fields(options: dict) -> None:
    pass


def _convert_v11(options: dict) -> None:
    options.pop("layout_configuration", None)
    options.pop("patcher_configuration", None)


def _convert_v12(options: dict) -> None:
    if "cosmetic_patches" in options:
        options["cosmetic_patches"]["unvisited_room_names"] = True


def _convert_v13(options: dict) -> None:
    cosmetic_patches = options.pop("cosmetic_patches", None)
    output_directory = options.pop("output_directory", None)

    if cosmetic_patches is not None or output_directory is not None:
        if cosmetic_patches is None:
            cosmetic_patches = {
                "disable_hud_popup": True,
                "speed_up_credits": True,
                "open_map": True,
                "force_fusion": False,
                "unvisited_room_names": True,
                "pickup_markers": True,
                "teleporter_sounds": True,
                "user_preferences": {
                    "sound_mode": 1,
                    "screen_brightness": 4,
                    "screen_x_offset": 0,
                    "screen_y_offset": 0,
                    "screen_stretch": 0,
                    "sfx_volume": 105,
                    "music_volume": 79,
                    "hud_alpha": 255,
                    "helmet_alpha": 255,
                    "hud_lag": False,
                    "invert_y_axis": False,
                    "rumble": True,
                    "hint_system": False,
                },
            }
        options["per_game_options"] = {
            "prime2": {
                "cosmetic_patches": cosmetic_patches,
                "input_path": None,
                "output_directory": output_directory,
                "output_format": None,
            }
        }


def _convert_v14(options: dict) -> None:
    for game_options in options.get("per_game_options", {}).values():
        game_options["output_format"] = None


def _convert_v15(options: dict) -> None:
    per_game_options = options.get("per_game_options", {})
    if "prime1" in per_game_options and "cosmetic_patches" in per_game_options["prime1"]:
        per_game_options["prime1"]["cosmetic_patches"].pop("debug_pickups", None)


def _convert_v16(options: dict) -> None:
    per_game_options = options.pop("per_game_options", {})

    for game_name in ["prime1", "prime2", "cave_story"]:
        if game_name in per_game_options:
            options[f"game_{game_name}"] = per_game_options[game_name]


def _convert_v17(options: dict) -> None:
    for game_name in ["prime1", "prime2"]:
        if f"game_{game_name}" in options:
            options[f"game_{game_name}"]["use_external_models"] = []


def _convert_v20(options: dict) -> None:
    # added experimental settings
    options.get("game_prime1", {}).get("cosmetic_patches", {}).pop("qol_cosmetic", None)


def _convert_v21(options: dict) -> None:
    # multiple connectors
    options["connector_builders"] = []

    nintendont_ip = options.pop("nintendont_ip", None)
    choice = options.get("game_backend")
    params = {}
    if choice == "nintendont":
        params = {"ip": nintendont_ip}
        if (params["ip"] or "") == "":
            choice = None

    if choice is not None:
        options["connector_builders"].append(
            {
                "choice": choice,
                "params": params,
            }
        )


def _convert_v23(options: dict) -> None:
    if "cosmetic_patches" in options.get("game_prime2", {}):
        options["game_prime2"]["cosmetic_patches"].pop("teleporter_sounds", None)


def _dread_linux_ryujinx_path(options: dict) -> None:
    if "game_dread" in options:
        options["game_dread"]["linux_ryujinx_path"] = "flatpak"


def _msr_cosmetic_laser_color(options: dict) -> None:
    if "cosmetic_patches" in options.get("game_samus_returns", {}):
        options["game_samus_returns"]["cosmetic_patches"].pop("use_grapple_laser_color", None)


def _msr_exheader_path(options: dict) -> None:
    if "game_samus_returns" in options:
        options["game_samus_returns"]["input_exheader"] = None


def _msr_room_names_visible(options: dict) -> None:
    if "game_samus_returns" in options:
        options["game_samus_returns"]["cosmetic_patches"]["show_room_names"] = "ALWAYS"


def _remove_msr_fields(options: dict) -> None:
    if "game_samus_returns" in options:
        options["game_samus_returns"].pop("input_directory", None)
        options["game_samus_returns"].pop("input_exheader", None)
        options["game_samus_returns"].pop("target_version", None)
        options["game_samus_returns"]["input_file"] = None


def _msr_enable_remote_lua(options: dict) -> None:
    if "cosmetic_patches" in options.get("game_samus_returns", {}):
        options["game_samus_returns"]["cosmetic_patches"].pop("enable_remote_lua", None)


_CONVERTER_FOR_VERSION = [
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    _convert_v11,
    _convert_v12,
    _convert_v13,
    _convert_v14,
    _convert_v15,
    _convert_v16,
    _convert_v17,
    _only_new_fields,  # added parent_for_presets
    _only_new_fields,  # added Dread's show_death_counter
    _convert_v20,
    _convert_v21,
    _only_new_fields,  # added preset order
    _convert_v23,
    _only_new_fields,  # added Dread's missile pack recolor
    _only_new_fields,  # added Dread's auto tracker
    _only_new_fields,  # added allow_crash_reporting
    _only_new_fields,  # added DebugConnectorBuilder's layout_uuid
    _only_new_fields,  # added Dread's music sliders
    _only_new_fields,  # added Dread's "Access Permanently Closed" alt-shield
    _dread_linux_ryujinx_path,  # added Dread Ryujinx export to Unix systems
    _msr_cosmetic_laser_color,  # remove the Grapple Laser color checkbox for MSR Cosmetics
    _msr_exheader_path,  # adds empty exheader path for MSR
    _msr_room_names_visible,  # forces room name display to be on by default
    _only_new_fields,  # Adds tileset+background rotation for AM2R
    _only_new_fields,  # added MSR's music shuffle cosemetic option
    _only_new_fields,  # added MSR's music sliders
    _remove_msr_fields,  # removes MSR's exheader and input field
    _only_new_fields,  # added last_changelog_displayed_dev
    _msr_enable_remote_lua,  # removes enable_remote_lua as it'll always be enabled
]
_CURRENT_OPTIONS_FILE_VERSION = migration_lib.get_version(_CONVERTER_FOR_VERSION)


# debug_locations_check


def get_persisted_options_from_data(persisted_data: dict) -> dict:
    options = persisted_data.get("options", {})
    options["schema_version"] = persisted_data.get("version", 0)

    return migration_lib.apply_migrations(
        options,
        _CONVERTER_FOR_VERSION,
    )


def serialized_data_for_options(data_to_persist: dict) -> dict:
    return {"version": _CURRENT_OPTIONS_FILE_VERSION, "options": data_to_persist}


def _try_read_file(file_path: Path) -> str | None:
    try:
        contents = file_path.read_text("utf-8")
        if contents.strip() == "":
            return None
        return contents
    except FileNotFoundError:
        return None


def find_config_files(data_path: Path) -> Iterator[str]:
    for version in range(_CURRENT_OPTIONS_FILE_VERSION, _FIRST_VERSION_IN_SUBFOLDER - 1, -1):
        if (result := _try_read_file(data_path.joinpath("versioned_config", f"{version}.json"))) is not None:
            yield result

    if (result := _try_read_file(data_path.joinpath("config.json"))) is not None:
        yield result


def replace_config_file_with(data_path: Path, new_data: dict):
    # Write to a separate file, so we don't corrupt the existing one in case we unexpectedly
    # are unable to finish writing the file
    new_config_path = data_path.joinpath("config_new.json")
    json_lib.write_path(new_config_path, new_data)

    # Place the new, complete, config to the desired path
    config_path = data_path.joinpath("versioned_config", f"{_CURRENT_OPTIONS_FILE_VERSION}.json")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    new_config_path.replace(config_path)
