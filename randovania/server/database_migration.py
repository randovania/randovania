import peewee
import playhouse.migrate

from randovania.server import database


def add_ready_field(migrator: playhouse.migrate.SqliteMigrator):
    with database.db.atomic():
        playhouse.migrate.migrate(
            migrator.add_column("multiplayer_membership", "ready", database.MultiplayerMembership.ready),
        )


def rename_state_to_visibility(migrator: playhouse.migrate.SqliteMigrator):
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


_migrations = {
    database.DatabaseMigrations.ADD_READY_TO_MEMBERSHIP: add_ready_field,
    database.DatabaseMigrations.SESSION_STATE_TO_VISIBILITY: rename_state_to_visibility,
}


def apply_migrations():
    migrator = playhouse.migrate.SqliteMigrator(database.db)

    all_performed = {performed.migration for performed in database.PerformedDatabaseMigrations.select()}

    for enum_value, call in _migrations.items():
        if enum_value not in all_performed:
            call(migrator)
            database.PerformedDatabaseMigrations.create(
                migration=enum_value,
            )
