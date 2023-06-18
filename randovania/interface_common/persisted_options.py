from pathlib import Path
from typing import Iterator

from randovania.lib import migration_lib, json_lib

_FIRST_VERSION_IN_SUBFOLDER = 18


def _convert_v11(options: dict) -> dict:
    options.pop("layout_configuration", None)
    options.pop("patcher_configuration", None)

    return options


def _convert_v12(options: dict) -> dict:
    if "cosmetic_patches" in options:
        options["cosmetic_patches"]["unvisited_room_names"] = True

    return options


def _convert_v13(options: dict) -> dict:
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
                    "hint_system": False
                }
            }
        options["per_game_options"] = {
            "prime2": {
                "cosmetic_patches": cosmetic_patches,
                "input_path": None,
                "output_directory": output_directory,
                "output_format": None,
            }
        }

    return options


def _convert_v14(options: dict) -> dict:
    for game_options in options.get("per_game_options", {}).values():
        game_options["output_format"] = None

    return options


def _convert_v15(options: dict) -> dict:
    per_game_options = options.get("per_game_options", {})
    if "prime1" in per_game_options and "cosmetic_patches" in per_game_options["prime1"]:
        per_game_options["prime1"]["cosmetic_patches"].pop("debug_pickups", None)

    return options


def _convert_v16(options: dict) -> dict:
    per_game_options = options.pop("per_game_options", {})

    for game_name in ["prime1", "prime2", "cave_story"]:
        if game_name in per_game_options:
            options[f"game_{game_name}"] = per_game_options[game_name]

    return options


def _convert_v17(options: dict) -> dict:
    for game_name in ["prime1", "prime2"]:
        if f"game_{game_name}" in options:
            options[f"game_{game_name}"]["use_external_models"] = []

    return options


def _convert_v18(options: dict) -> dict:
    # added parent_for_presets, but we don't have to change anything.
    # we added a new version to split the file
    return options


def _convert_v19(options: dict) -> dict:
    # added Dread's show_death_counter
    return options


def _convert_v20(options: dict) -> dict:
    # added experimental settings
    options.get("game_prime1", {}).get("cosmetic_patches", {}).pop("qol_cosmetic", None)
    return options


def _convert_v21(options: dict) -> dict:
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
        options["connector_builders"].append({
            "choice": choice,
            "params": params,
        })

    return options


def _convert_v22(options: dict) -> dict:
    # added preset order
    return options


def _convert_v23(options: dict) -> dict:
    if "cosmetic_patches" in options.get("game_prime2", {}):
        options["game_prime2"]["cosmetic_patches"].pop("teleporter_sounds", None)

    return options

def _convert_v24(options: dict) -> dict:
    # added Dread's missile pack recolor
    return options

def _convert_v25(options: dict) -> dict:
    # added Dread's auto tracker
    return options

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
    _convert_v18,
    _convert_v19,
    _convert_v20,
    _convert_v21,
    _convert_v22,
    _convert_v23,
    _convert_v24,
    _convert_v25,
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
    return {
        "version": _CURRENT_OPTIONS_FILE_VERSION,
        "options": data_to_persist
    }


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
