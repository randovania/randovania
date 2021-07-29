import randovania

SERVER_API_VERSION = 4


def connection_headers():
    from randovania.layout.preset_migration import CURRENT_PRESET_VERSION
    from randovania.layout.permalink import Permalink
    from randovania.layout.layout_description import CURRENT_DESCRIPTION_SCHEMA_VERSION
    return {
        "X-Randovania-Version": randovania.VERSION,
        "X-Randovania-API-Version": str(SERVER_API_VERSION),
        "X-Randovania-Preset-Version": str(CURRENT_PRESET_VERSION),
        "X-Randovania-Permalink-Version": str(Permalink.current_version()),
        "X-Randovania-Description-Version": str(CURRENT_DESCRIPTION_SCHEMA_VERSION),
    }
