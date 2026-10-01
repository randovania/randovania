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


def add_world_abandoned_fields(migrator: playhouse.migrate.SqliteMigrator) -> None:
    with database.db.atomic():
        database.db.execute(
            migrator._alter_table(migrator.make_context(), "world")
            .literal(" ADD ")
            .sql(peewee.Entity("abandoned"))
            .literal(" INTEGER NOT NULL DEFAULT(0)")  # SQLite saves boolean values as integers
        )
        database.db.execute(
            migrator._alter_table(migrator.make_context(), "multiplayer_session")
            .literal(" ADD ")
            .sql(peewee.Entity("allow_abandon_worlds"))
            .literal(" INTEGER NOT NULL DEFAULT(1)")
        )


def _add_not_null_column(migrator: playhouse.migrate.SqliteMigrator, table: str, column: str, definition: str) -> None:
    database.db.execute(
        migrator._alter_table(migrator.make_context(), table)
        .literal(" ADD ")
        .sql(peewee.Entity(column))
        .literal(f" {definition}")
    )


def add_async_race_teams(migrator: playhouse.migrate.SqliteMigrator) -> None:
    with database.db.atomic():
        if database.db.table_exists("async_race_room"):
            database.db.create_tables([database.AsyncRaceTeam])

            _add_not_null_column(migrator, "async_race_entry", "has_exported", "INTEGER NOT NULL DEFAULT(0)")
            playhouse.migrate.migrate(
                migrator.drop_not_null("async_race_entry_pause", "entry_id"),
                migrator.add_column("async_race_entry", "team_id", database.AsyncRaceEntry.team),
                migrator.add_column("async_race_entry_pause", "team_id", database.AsyncRaceEntryPause.team),
            )

            # ensure that (user_id, room_id) is unique which was not forced before
            earliest_entries = "SELECT MIN(id) FROM async_race_entry GROUP BY room_id, user_id"
            database.db.execute_sql(f"DELETE FROM async_race_entry_pause WHERE entry_id NOT IN ({earliest_entries})")
            database.db.execute_sql(f"DELETE FROM async_race_entry WHERE id NOT IN ({earliest_entries})")

            playhouse.migrate.migrate(migrator.add_index("async_race_entry", ("room_id", "user_id"), unique=True))

        playhouse.migrate.migrate(
            migrator.add_column("multiplayer_session", "race_team_id", database.MultiplayerSession.race_team)
        )


def add_async_race_session_settings(migrator: playhouse.migrate.SqliteMigrator) -> None:
    with database.db.atomic():
        if not database.db.table_exists("async_race_room"):
            return

        _add_not_null_column(migrator, "async_race_room", "allow_coop", "INTEGER NOT NULL DEFAULT(0)")
        _add_not_null_column(migrator, "async_race_room", "allow_abandon_worlds", "INTEGER NOT NULL DEFAULT(0)")
        _add_not_null_column(migrator, "async_race_room", "shared_team_timer", "INTEGER NOT NULL DEFAULT(1)")


_migrations = {
    database.DatabaseMigrations.ADD_READY_TO_MEMBERSHIP: add_ready_field,
    database.DatabaseMigrations.SESSION_STATE_TO_VISIBILITY: rename_state_to_visibility,
    database.DatabaseMigrations.ADD_GAME_BEATEN: add_game_beaten_field,
    database.DatabaseMigrations.ADD_WORLD_ABANDONED: add_world_abandoned_fields,
    database.DatabaseMigrations.ADD_ASYNC_RACE_TEAMS: add_async_race_teams,
    database.DatabaseMigrations.ADD_ASYNC_RACE_SESSION_SETTINGS: add_async_race_session_settings,
}


def apply_migrations() -> None:
    migrator = playhouse.migrate.SqliteMigrator(database.db)

    all_performed = {
        performed.migration
        for performed in database.PerformedDatabaseMigrations.select().where(
            # Filter migrations for enum values that don't exist (such as removed ones, or made in a branch)
            # `<<` operator means `X in Y`: https://peewee.readthedocs.io/en/latest/peewee/query_operators.html#query-operators
            database.PerformedDatabaseMigrations.migration << list(_migrations.keys())
        )
    }

    for enum_value, call in _migrations.items():
        if enum_value not in all_performed:
            call(migrator)
            database.PerformedDatabaseMigrations.create(
                migration=enum_value,
            )
