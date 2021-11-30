import randovania

SERVER_API_VERSION = 4


def connection_headers():
    from randovania.layout.layout_description import CURRENT_DESCRIPTION_SCHEMA_VERSION
    from randovania.layout import preset_migration, permalink
    return {
        "X-Randovania-Version": randovania.VERSION,
        "X-Randovania-API-Version": str(SERVER_API_VERSION),
        "X-Randovania-Preset-Version": str(preset_migration.CURRENT_VERSION),
        "X-Randovania-Permalink-Version": str(permalink.Permalink.current_version()),
        "X-Randovania-Description-Version": str(CURRENT_DESCRIPTION_SCHEMA_VERSION),
    }
