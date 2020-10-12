import pytest

from randovania.layout.preset_migration import VersionedPreset, CURRENT_PRESET_VERSION


@pytest.mark.asyncio
async def test_migration(test_files_dir):
    preset = await VersionedPreset.from_file(test_files_dir.joinpath("presets", "fewest_changes_v1.rdvpreset"))
    assert preset.data["schema_version"] == 1
    assert preset.as_json["schema_version"] == 1
    preset.ensure_converted()
    assert preset.as_json["schema_version"] == CURRENT_PRESET_VERSION
