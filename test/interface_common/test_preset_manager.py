import dulwich.repo
import pytest

from randovania.interface_common import preset_manager
from randovania.layout.preset_migration import VersionedPreset


@pytest.mark.asyncio
async def test_add_then_delete_preset(tmp_path, default_preset):
    p = VersionedPreset.with_preset(default_preset.fork())

    dulwich.repo.Repo.init(tmp_path)
    manager = preset_manager.PresetManager(tmp_path.joinpath("presets"))
    await manager.load_user_presets()

    assert manager.preset_for_uuid(p.uuid) is None
    manager.add_new_preset(p)
    assert manager.preset_for_uuid(p.uuid) == p
    manager.delete_preset(p)
    assert manager.preset_for_uuid(p.uuid) is None

