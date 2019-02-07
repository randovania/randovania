_CURRENT_OPTIONS_FILE_VERSION = 6


def _convert_logic(layout_logic: str) -> str:
    if layout_logic == "no-glitches":
        return "no-tricks"
    return layout_logic


def _convert_v1(options: dict) -> dict:
    results = {}

    try:
        results["patcher_configuration"] = {
            "disable_hud_popup": options["hud_memo_popup_removal"],
            "menu_mod": options["include_menu_mod"],
        }
    except KeyError as e:
        print("Unable to port patcher_configuration to new version, got {}".format(e))

    try:
        results["layout_configuration"] = {
            "trick_level": _convert_logic(options["layout_logic"]),
            "sky_temple_keys": options["layout_sky_temple_keys"],
            "item_loss": options["layout_item_loss"],
            "elevators": options["layout_elevators"],
            "pickup_quantities": options["quantity_for_pickup"],
        }
    except KeyError as e:
        print("Unable to port layout_configuration to new version, got {}".format(e))

    return results


def _convert_v2(options: dict) -> dict:
    if "layout_configuration" in options:
        layout_configuration = options["layout_configuration"]
        if layout_configuration.get("sky_temple_keys") == "randomized":
            layout_configuration["sky_temple_keys"] = "fully-random"

    return options


def _convert_v3(options: dict) -> dict:
    if "layout_configuration" in options:
        layout_configuration = options["layout_configuration"]

        if layout_configuration.pop("item_loss", None) == "disabled":
            layout_configuration["starting_resources"] = "vanilla-item-loss-disabled"
        else:
            layout_configuration["starting_resources"] = "vanilla-item-loss-enabled"

        layout_configuration["starting_location"] = "ship"

    if "patcher_configuration" in options:
        options["patcher_configuration"]["speed_up_credits"] = True

    return options


def _convert_v4(options: dict) -> dict:
    if "patcher_configuration" in options:
        patcher_config = options["patcher_configuration"]
        options["cosmetic_patches"] = {
            "disable_hud_popup": patcher_config.pop("disable_hud_popup"),
            "speed_up_credits": patcher_config.pop("speed_up_credits"),
        }

    return options


def _convert_v5(options: dict) -> dict:
    if "patcher_configuration" in options:
        options["patcher_configuration"]["warp_to_start"] = True

    return options


_CONVERTER_FOR_VERSION = {
    1: _convert_v1,
    2: _convert_v2,
    3: _convert_v3,
    4: _convert_v4,
    5: _convert_v5,
}


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
