CURRENT_PRESET_VERSION = 2


def _migrate_v1(preset: dict) -> dict:
    layout_configuration = preset["layout_configuration"]
    layout_configuration["beam_configuration"] = {
        "power": {
            "item_index": 0,
            "ammo_a": -1,
            "ammo_b": -1,
            "uncharged_cost": 0,
            "charged_cost": 0,
            "combo_missile_cost": 5,
            "combo_ammo_cost": 0
        },
        "dark": {
            "item_index": 1,
            "ammo_a": 45,
            "ammo_b": -1,
            "uncharged_cost": 1,
            "charged_cost": 5,
            "combo_missile_cost": 5,
            "combo_ammo_cost": 30
        },
        "light": {
            "item_index": 2,
            "ammo_a": 46,
            "ammo_b": -1,
            "uncharged_cost": 1,
            "charged_cost": 5,
            "combo_missile_cost": 5,
            "combo_ammo_cost": 30
        },
        "annihilator": {
            "item_index": 3,
            "ammo_a": 46,
            "ammo_b": 45,
            "uncharged_cost": 1,
            "charged_cost": 5,
            "combo_missile_cost": 5,
            "combo_ammo_cost": 30
        }
    }
    layout_configuration["skip_final_bosses"] = False
    layout_configuration["energy_per_tank"] = 100.0
    return preset


_MIGRATIONS = {
    1: _migrate_v1,
}


def _apply_migration(preset: dict, version: int) -> dict:
    while version < CURRENT_PRESET_VERSION:
        preset = _MIGRATIONS[version](preset)
        version += 1
    return preset


def convert_to_current_version(preset: dict) -> dict:
    schema_version = preset["schema_version"]
    if schema_version > CURRENT_PRESET_VERSION:
        raise ValueError(f"Unknown version: {schema_version}")

    if schema_version < CURRENT_PRESET_VERSION:
        return _apply_migration(preset, schema_version)
    else:
        return preset
