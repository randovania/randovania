import json
import logging

import peewee
import playhouse.migrate

from randovania.server import database


def add_ready_field(migrator: playhouse.migrate.SqliteMigrator) -> None:
    with database.db.atomic():
        playhouse.migrate.migrate(
            migrator.add_column("multiplayer_membership", "ready", database.MultiplayerMembership.ready),
        )


def rename_state_to_visibility(migrator: playhouse.migrate.SqliteMigrator) -> None:
    with database.db.atomic():
        database.db.execute(
            migrator._alter_table(migrator.make_context(), "multiplayer_session")
            .literal(" RENAME COLUMN ")
            .sql(peewee.Entity("state"))
            .literal(" TO ")
            .sql(peewee.Entity("visibility"))
        )
        database.db.execute_sql(
            "UPDATE multiplayer_session SET visibility='visible' WHERE visibility='setup' OR visibility='in-progress'"
        )
        database.db.execute_sql("UPDATE multiplayer_session SET visibility='hidden' WHERE visibility='finished'")


def add_game_beaten_field(migrator: playhouse.migrate.SqliteMigrator) -> None:
    with database.db.atomic():
        database.db.execute(
            migrator._alter_table(migrator.make_context(), "world")
            .literal(" ADD ")
            .sql(peewee.Entity("beaten"))
            .literal(" INTEGER NOT NULL DEFAULT(0)")  # SQLite saves boolean values as integers
        )


def add_world_preset_sha256_field(migrator: playhouse.migrate.SqliteMigrator) -> None:
    with database.db.atomic():
        playhouse.migrate.migrate(
            migrator.alter_add_column(
                database.World._meta.table_name,  # type: ignore[attr-defined]
                database.World.preset_data.column_name,  # type: ignore[attr-defined]
                database.World.preset_data,
            )
        )


def migrate_world_preset(migrator: playhouse.migrate.SqliteMigrator) -> None:
    query = database.World.select()
    world_count = query.count()

    for i, world in enumerate(query):
        if i % 50 == 0:
            logging.warning("Converting World.preset to PresetData. At %s of %s.", i + 1, world_count)
        world.preset_data = database.PresetData.create_for_json(json.loads(world.preset))
        world.save()


_migrations = {
    database.DatabaseMigrations.ADD_READY_TO_MEMBERSHIP: add_ready_field,
    database.DatabaseMigrations.SESSION_STATE_TO_VISIBILITY: rename_state_to_visibility,
    database.DatabaseMigrations.ADD_GAME_BEATEN: add_game_beaten_field,
    database.DatabaseMigrations.ADD_WORLD_PRESET_SHA256: add_world_preset_sha256_field,
    database.DatabaseMigrations.MIGRATE_WORLD_PRESET: migrate_world_preset,
}


def apply_migrations() -> None:
    migrator = playhouse.migrate.SqliteMigrator(database.db)

    all_performed = {performed.migration for performed in database.PerformedDatabaseMigrations.select()}

    for enum_value, call in _migrations.items():
        if enum_value not in all_performed:
            call(migrator)
            database.PerformedDatabaseMigrations.create(
                migration=enum_value,
            )
