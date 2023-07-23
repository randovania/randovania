import playhouse.migrate

from randovania.server import database


def add_ready_field(migrator: playhouse.migrate.SqliteMigrator):
    with database.db.atomic():
        playhouse.migrate.migrate(
            migrator.add_column("multiplayer_membership", "ready",
                                database.MultiplayerMembership.ready),
        )


_migrations = {
    database.DatabaseMigrations.ADD_READY_TO_MEMBERSHIP: add_ready_field,
}


def apply_migrations():
    migrator = playhouse.migrate.SqliteMigrator(database.db)

    all_performed = {
        performed.migration
        for performed in database.PerformedDatabaseMigrations.select()
    }

    for enum_value, call in _migrations.items():
        if enum_value not in all_performed:
            call(migrator)
            database.PerformedDatabaseMigrations.create(
                migration=enum_value,
            )
