import randovania

SERVER_API_VERSION = 5


def connection_headers():
    from randovania.layout import preset_migration, permalink, description_migration
    return {
        "X-Randovania-Version": randovania.VERSION,
        "X-Randovania-API-Version": str(SERVER_API_VERSION),
        "X-Randovania-Preset-Version": str(preset_migration.CURRENT_VERSION),
        "X-Randovania-Permalink-Version": str(permalink.Permalink.current_schema_version()),
        "X-Randovania-Description-Version": str(description_migration.CURRENT_VERSION),
    }
