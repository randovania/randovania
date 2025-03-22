from __future__ import annotations

import copy
import functools
import typing

if typing.TYPE_CHECKING:
    from randovania.game.game_enum import RandovaniaGame


class UnsupportedVersion(ValueError):
    pass


class Migration(typing.Protocol):
    def __call__(self, __data: dict) -> None: ...


class GameMigration(typing.Protocol):
    def __call__(self, __data: dict, game: RandovaniaGame) -> None: ...


Migrations = typing.Sequence[Migration | None]
GameMigrations = typing.Sequence[GameMigration | None]


def apply_migrations(
    data: dict, migrations: Migrations, *, copy_before_migrating: bool = False, version_name: str = "version"
) -> dict:
    schema_version = typing.cast("int", data.get("schema_version", 1))
    version = get_version(migrations)

    while schema_version < version:
        if copy_before_migrating:
            data = copy.deepcopy(data)
            copy_before_migrating = False

        apply_migration = migrations[schema_version - 1]
        if apply_migration is None:
            raise UnsupportedVersion(
                f"Requested a migration from {version_name} {schema_version}, but it's no longer supported. "
                f"You can try using an older Randovania version."
            )

        apply_migration(data)
        schema_version += 1

    if schema_version > version:
        raise UnsupportedVersion(
            f"Found {version_name} {schema_version}, but only up to {version} is supported. "
            f"This file was created using a newer Randovania version."
        )

    data["schema_version"] = schema_version

    return data


def apply_migrations_with_game(
    data: dict,
    migrations: GameMigrations,
    game: RandovaniaGame,
    *,
    copy_before_migrating: bool = False,
    version_name: str = "version",
) -> dict:
    partialed_migrations = [
        None if migration is None else functools.partial(migration, game=game) for migration in migrations
    ]
    return apply_migrations(
        data, partialed_migrations, copy_before_migrating=copy_before_migrating, version_name=version_name
    )


def get_version(migrations: Migrations | GameMigrations) -> int:
    return len(migrations) + 1
