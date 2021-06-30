_CURRENT_OPTIONS_FILE_VERSION = 16


def _convert_logic(layout_logic: str) -> str:
    if layout_logic == "no-glitches":
        return "no-tricks"
    return layout_logic


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


_CONVERTER_FOR_VERSION = {
    11: _convert_v11,
    12: _convert_v12,
    13: _convert_v13,
    14: _convert_v14,
    15: _convert_v15,
}


# debug_locations_check

def get_persisted_options_from_data(persisted_data: dict) -> dict:
    version = persisted_data.get("version", 0)
    options = persisted_data.get("options")

    if not isinstance(options, dict):
        print("Data has no options.")
        return {}

    while version < _CURRENT_OPTIONS_FILE_VERSION:
        converter = _CONVERTER_FOR_VERSION.get(version)
        if converter is None:
            print("Converter not found for version '{}'".format(version))
            return {}

        options = converter(options)
        version += 1

    if version > _CURRENT_OPTIONS_FILE_VERSION:
        print("Options has an version from the future '{}'. Supported is only up to {}".format(
            version, _CURRENT_OPTIONS_FILE_VERSION))
        return {}

    return options


def serialized_data_for_options(data_to_persist: dict) -> dict:
    return {
        "version": _CURRENT_OPTIONS_FILE_VERSION,
        "options": data_to_persist
    }
