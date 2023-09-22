from __future__ import annotations

import pytest

from randovania.interface_common import preset_manager
from randovania.layout import preset_migration
from randovania.layout.versioned_preset import VersionedPreset


@pytest.mark.parametrize(
    ("preset_name", "schema_version"),
    [
        ("fewest_changes_v1.rdvpreset", 1),
        ("echoes-v44-migration-preset.rdvpreset", 44),
    ],
)
async def test_migration(test_files_dir, preset_name, schema_version):
    preset = await VersionedPreset.from_file(test_files_dir.joinpath("presets", preset_name))
    assert preset.data["schema_version"] == schema_version
    assert preset.as_json["schema_version"] == schema_version
    preset.ensure_converted()
    assert preset.as_json["schema_version"] == preset_migration.CURRENT_VERSION


@pytest.mark.parametrize("f", [pytest.param(f, id=f.name) for f in preset_manager.read_preset_list()])
def test_included_presets_are_valid(f):
    VersionedPreset.from_file_sync(f).get_preset()
