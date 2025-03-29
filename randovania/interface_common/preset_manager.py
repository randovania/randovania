from __future__ import annotations

import asyncio
import datetime
import logging
import time
import typing
from pathlib import Path

import dulwich.porcelain
import dulwich.repo
from dulwich.objects import Blob

import randovania
from randovania.game.game_enum import RandovaniaGame
from randovania.layout.versioned_preset import VersionedPreset
from randovania.lib import enum_lib

if typing.TYPE_CHECKING:
    import uuid
    from collections.abc import Iterator


def read_preset_list() -> list[Path]:
    preset_list = []
    for game in enum_lib.iterate_enum(RandovaniaGame):
        base_path = game.data_path.joinpath("presets")
        preset_list.extend([base_path.joinpath(preset["path"]) for preset in game.data.presets])

    return preset_list


def _commit(message: str, file_path: Path, repository: Path, remove: bool):
    with dulwich.porcelain.open_repo_closing(repository) as r:
        r = typing.cast("dulwich.repo.Repo", r)

        # Detect invalid index
        try:
            r.open_index()
        except Exception:
            Path(r.index_path()).unlink()
            r.reset_index()

    author = "randovania <nobody@example.com>"
    if remove:
        dulwich.porcelain.remove(repository, [file_path])
    else:
        dulwich.porcelain.add(repository, [file_path])

    dulwich.porcelain.commit(
        repository, message=f"{message} using Randovania v{randovania.VERSION}", author=author, committer=author
    )


def _get_preset_at_version(repository: Path, commit_sha: bytes, file_path: Path) -> str:
    blob = dulwich.porcelain.get_object_by_path(
        repository,
        dulwich.porcelain.path_to_tree_path(repository, file_path),
        commit_sha,
    )
    assert isinstance(blob, Blob)
    return blob.as_raw_string().decode()


def _history_for_file(repository: Path, file_path: Path) -> Iterator[tuple[datetime.datetime, bytes]]:
    from dulwich.objects import Commit
    from dulwich.walk import WalkEntry

    with dulwich.porcelain.open_repo_closing(repository) as r:
        r = typing.cast("dulwich.repo.Repo", r)

        paths = [dulwich.porcelain.path_to_tree_path(repository, file_path)]
        walker = r.get_walker(paths=paths)
        for entry in walker:
            assert isinstance(entry, WalkEntry)
            assert isinstance(entry.commit, Commit)
            yield datetime.datetime(*time.gmtime(entry.commit.commit_time)[:6]), entry.commit.id


class PresetManager:
    included_presets: dict[uuid.UUID, VersionedPreset]
    custom_presets: dict[uuid.UUID, VersionedPreset]
    _data_dir: Path | None
    _fallback_dir: Path | None

    def __init__(self, data_dir: Path | None):
        self.logger = logging.getLogger("PresetManager")
        self.included_presets = {
            preset.uuid: preset for preset in [VersionedPreset.from_file_sync(f) for f in read_preset_list()]
        }
        for preset in self.included_presets.values():
            preset.is_included_preset = True

        self.custom_presets = {}
        if data_dir is not None:
            self._data_dir = data_dir
        else:
            self._data_dir = None

    async def load_user_presets(self):
        all_files = self._data_dir.glob(f"*.{VersionedPreset.file_extension()}")
        user_presets = await asyncio.gather(*[VersionedPreset.from_file(f) for f in all_files])
        for preset in typing.cast("list[VersionedPreset]", user_presets):
            if preset.is_for_known_game():
                self.custom_presets[preset.uuid] = preset

    @property
    def data_dir(self):
        return self._data_dir

    @property
    def default_preset(self) -> VersionedPreset:
        for preset in self.included_presets.values():
            return preset
        raise ValueError("No included presets")

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

    def _get_repository_root(self):
        return self._data_dir.parent

    def _commit(self, message: str, file_path: Path, remove: bool):
        repo_root = self._get_repository_root()
        try:
            self.logger.info("Will perform git operation: %s for path %s", message, str(file_path))
            _commit(message, file_path, repo_root, remove)
            self.logger.debug("Git operation successful.")
        except Exception as e:
            self.logger.warning(f"Error committing change to presets: {e}", exc_info=e)

    def add_new_preset(self, new_preset: VersionedPreset) -> bool:
        """
        Adds a new custom preset.
        :param: new_preset
        :return True, if there wasn't any preset with that name
        """
        assert new_preset.uuid not in self.included_presets
        existed_before = new_preset.uuid in self.custom_presets
        self.custom_presets[new_preset.uuid] = new_preset

        path = self._file_path_for_preset(new_preset)
        new_preset.save_to_file(path)
        self._commit(f"Update preset '{new_preset.name}'", path, False)

        return not existed_before

    def delete_preset(self, preset: VersionedPreset):
        del self.custom_presets[preset.uuid]
        path = self._file_path_for_preset(preset)
        path.unlink()
        self._commit(f"Remove preset '{preset.name}'", path, True)

    def included_preset_with(self, game: RandovaniaGame, name: str) -> VersionedPreset | None:
        for preset in self.included_presets.values():
            if preset.game == game and preset.name == name:
                return preset

        return None

    def reference_preset_for_game(self, game: RandovaniaGame) -> VersionedPreset:
        reference_name = game.data.permalink_reference_preset
        if reference_name is None:
            return self.default_preset_for_game(game)
        else:
            return self.included_preset_with(game, reference_name)

    def preset_for_uuid(self, the_uid: uuid.UUID) -> VersionedPreset | None:
        return self.included_presets.get(the_uid, self.custom_presets.get(the_uid))

    def _file_path_for_preset(self, preset: VersionedPreset) -> Path:
        return self._data_dir.joinpath(f"{preset.uuid}.{preset.file_extension()}")

    def is_included_preset_uuid(self, the_uid: uuid.UUID) -> bool:
        return the_uid in self.included_presets

    def get_previous_versions(self, preset: VersionedPreset) -> Iterator[tuple[datetime.datetime, bytes]]:
        yield from _history_for_file(
            self._get_repository_root(),
            self._file_path_for_preset(preset),
        )

    def get_previous_version(self, preset: VersionedPreset, version: bytes) -> str:
        return _get_preset_at_version(
            self._get_repository_root(),
            version,
            self._file_path_for_preset(preset),
        )
