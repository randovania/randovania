import asyncio
import json
import logging
import os
import typing
import uuid
from pathlib import Path
from typing import List, Optional, Iterator, Dict

import dulwich.porcelain
import dulwich.repo

import randovania
from randovania.games.game import RandovaniaGame
from randovania.layout.preset_migration import VersionedPreset, InvalidPreset


def read_preset_list() -> List[Path]:
    base_path = randovania.get_data_path().joinpath("presets")

    with base_path.joinpath("presets.json").open() as presets_file:
        preset_list = json.load(presets_file)["presets"]

    return [
        base_path.joinpath(preset["path"])
        for preset in preset_list
    ]


def _commit(message: str, file_path: Path, repository: Path, remove: bool):

    with dulwich.porcelain.open_repo_closing(repository) as r:
        r = typing.cast(dulwich.repo.Repo, r)
        # Detect invalid index
        try:
            r.open_index()
        except Exception:
            os.remove(r.index_path())
            r.reset_index()

    author = "randovania <nobody@example.com>"
    if remove:
        dulwich.porcelain.remove(repository, [file_path])
    else:
        dulwich.porcelain.add(repository, [file_path])

    dulwich.porcelain.commit(repository, message=f"{message} using Randovania v{randovania.VERSION}",
                             author=author, committer=author)


class PresetManager:
    included_presets: Dict[uuid.UUID, VersionedPreset]
    custom_presets: Dict[uuid.UUID, VersionedPreset]
    _data_dir: Optional[Path]
    _fallback_dir: Optional[Path]

    def __init__(self, data_dir: Optional[Path]):
        self.included_presets = {
            preset.uuid: preset
            for preset in [VersionedPreset.from_file_sync(f) for f in read_preset_list()]
        }

        self.custom_presets = {}
        if data_dir is not None:
            self._data_dir = data_dir
        else:
            self._data_dir = None

    async def load_user_presets(self):
        all_files = self._data_dir.glob(f"*.{VersionedPreset.file_extension()}")
        user_presets = await asyncio.gather(*[VersionedPreset.from_file(f) for f in all_files])
        for preset in typing.cast(List[VersionedPreset], user_presets):
            self.custom_presets[preset.uuid] = preset

    @property
    def default_preset(self) -> VersionedPreset:
        for preset in self.included_presets.values():
            return preset
        raise ValueError(f"No included presets")

    def default_preset_for_game(self, game: RandovaniaGame) -> VersionedPreset:
        for preset in self.included_presets.values():
            if preset.game == game:
                return preset
        raise ValueError(f"{game} has no included preset")

    def presets_for_game(self, game: RandovaniaGame) -> Iterator[VersionedPreset]:
        for preset in self.all_presets:
            if preset.game == game:
                yield preset

    @property
    def all_presets(self) -> Iterator[VersionedPreset]:
        yield from self.included_presets.values()
        yield from self.custom_presets.values()

    def _commit(self, message: str, file_path: Path, remove: bool):
        repo_root = self._data_dir.parent
        try:
            _commit(message, file_path, repo_root, remove)
        except Exception as e:
            logging.warning(f"Error committing change to presets: {e}", exc_info=e)

    def add_new_preset(self, new_preset: VersionedPreset) -> bool:
        """
        Adds a new custom preset.
        :param: new_preset
        :return True, if there wasn't any preset with that name
        """
        assert new_preset.uuid not in self.included_presets
        existed_before = new_preset.uuid in self.custom_presets
        self.custom_presets[new_preset.uuid] = new_preset

        path = self._file_name_for_preset(new_preset)
        new_preset.save_to_file(path)
        self._commit(f"Update preset '{new_preset.name}'", path, False)

        return not existed_before

    def delete_preset(self, preset: VersionedPreset):
        del self.custom_presets[preset.uuid]
        path = self._file_name_for_preset(preset)
        os.remove(path)
        self._commit(f"Remove preset '{preset.name}'", path, True)

    def included_preset_with(self, game: RandovaniaGame, name: str) -> Optional[VersionedPreset]:
        for preset in self.included_presets.values():
            if preset.game == game and preset.name == name:
                return preset

        return None

    def preset_for_uuid(self, the_uid: uuid.UUID) -> Optional[VersionedPreset]:
        return self.included_presets.get(the_uid, self.custom_presets.get(the_uid))

    def _file_name_for_preset(self, preset: VersionedPreset) -> Path:
        return self._data_dir.joinpath("{}.{}".format(preset.uuid, preset.file_extension()))

    def should_do_migration(self):
        if not self.custom_presets:
            from randovania.interface_common import persistence
            for _ in persistence.local_data_dir().joinpath("presets").glob("*.rdvpreset"):
                return True
        return False

    async def migrate_from_old_path(self, on_update):
        from randovania.interface_common import persistence

        files_to_commit = []

        all_files = list(persistence.local_data_dir().joinpath("presets").glob("*.rdvpreset"))

        for i, old_file in enumerate(all_files):
            on_update(i, len(all_files))
            preset = await VersionedPreset.from_file(old_file)
            try:
                preset.ensure_converted()
                path = self._file_name_for_preset(preset)
                preset.save_to_file(path)
                self.custom_presets[preset.uuid] = preset
                files_to_commit.append(path)
            except InvalidPreset as e:
                logging.info(f"Not migrating {preset.name}: {e}")
                continue

        on_update(len(all_files), len(all_files))
        dulwich.porcelain.add(self._data_dir.parent, files_to_commit)

        author = "randovania <nobody@example.com>"
        dulwich.porcelain.commit(self._data_dir.parent,
                                 message=f"Migrated old presets using Randovania v{randovania.VERSION}",
                                 author=author, committer=author)
