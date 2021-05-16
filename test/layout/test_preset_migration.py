import pytest

from randovania.interface_common import preset_manager
from randovania.layout.preset_migration import VersionedPreset, CURRENT_PRESET_VERSION


@pytest.mark.asyncio
async def test_migration(test_files_dir):
    preset = await VersionedPreset.from_file(test_files_dir.joinpath("presets", "fewest_changes_v1.rdvpreset"))
    assert preset.data["schema_version"] == 1
    assert preset.as_json["schema_version"] == 1
    preset.ensure_converted()
    assert preset.as_json["schema_version"] == CURRENT_PRESET_VERSION


@pytest.mark.parametrize("f", [
    pytest.param(f, id=f.name)
    for f in preset_manager.read_preset_list()
])
def test_included_presets_are_valid(f):
    VersionedPreset.from_file_sync(f).get_preset()
