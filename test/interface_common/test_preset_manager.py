from __future__ import annotations

import datetime
import tarfile

import dulwich.repo

from randovania.interface_common import preset_manager
from randovania.layout.versioned_preset import VersionedPreset


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


def test_get_preset_at_version(test_files_dir):
    # Setup
    preset_path = test_files_dir.joinpath("presets/fewest_changes_v1.rdvpreset")

    # Run
    result = preset_manager._get_preset_at_version(
        test_files_dir.root.parents[1],
        b"1f2a55862ce12938dfa806d2dbd35b346a0164d3",
        preset_path,
    )

    # Assert
    assert result != preset_path.read_text()
    VersionedPreset.from_str(result).get_preset()


def test_history_for_file(tmp_path, test_files_dir):
    # Setup
    tar_path = test_files_dir.joinpath("history_for_file_test.tar")
    with tarfile.TarFile(tar_path) as tar_file:
        tar_file.extractall(tmp_path)
    repository = tmp_path.joinpath("history_for_file_test")

    # Run
    result = list(
        preset_manager._history_for_file(
            repository,
            repository.joinpath("presets/fewest_changes_v1.rdvpreset"),
        )
    )

    # Assert
    assert result == [
        (datetime.datetime(2023, 5, 22, 15, 47, 17), b"eeed98b72a1738c72ed74eee2cbf33af234d3b07"),
        (datetime.datetime(2023, 5, 22, 15, 46, 49), b"37bd0129c1a5f97d71178b7d606dbcb6ff6cd211"),
    ]
