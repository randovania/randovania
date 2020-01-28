_CURRENT_OPTIONS_FILE_VERSION = 12


def _convert_logic(layout_logic: str) -> str:
    if layout_logic == "no-glitches":
        return "no-tricks"
    return layout_logic


def _convert_v11(options: dict) -> dict:
    options.pop("layout_configuration", None)
    options.pop("patcher_configuration", None)

    return options


_CONVERTER_FOR_VERSION = {
    11: _convert_v11,
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
