from unittest.mock import ANY

from randovania.network_common import multiplayer_session
from randovania.network_common.session_visibility import MultiplayerSessionVisibility
from randovania.server import database, database_migration


def test_migrations(empty_database):
    for sql in [
        'CREATE TABLE "user" ("id" INTEGER NOT NULL PRIMARY KEY, "discord_id" INTEGER, "name" VARCHAR(255) NOT NULL,'
        ' "admin" INTEGER NOT NULL)',
        'CREATE INDEX "user_discord_id" ON "user" ("discord_id")',
        'CREATE TABLE "multiplayer_session" ("id" INTEGER NOT NULL PRIMARY KEY, "name" VARCHAR(50) NOT NULL,'
        ' "password" VARCHAR(255), "state" VARCHAR(255) NOT NULL, "layout_description_json" BLOB,'
        ' "game_details_json" VARCHAR(255), "creator_id" INTEGER NOT NULL, "creation_date" DATETIME NOT NULL,'
        ' "generation_in_progress_id" INTEGER, "dev_features" VARCHAR(255), "allow_coop" INTEGER NOT NULL,'
        ' "allow_everyone_claim_world" INTEGER NOT NULL, FOREIGN KEY ("creator_id") REFERENCES "user" ("id"),'
        ' FOREIGN KEY ("generation_in_progress_id") REFERENCES "user" ("id"))',
        'CREATE INDEX "multiplayer_session_creator_id" ON "multiplayer_session" ("creator_id")',
        'CREATE INDEX "multiplayer_session_generation_in_progress_id" ON "multiplayer_session"'
        ' ("generation_in_progress_id")',
        'CREATE TABLE "multiplayer_audit_entry" ("id" INTEGER NOT NULL PRIMARY KEY, "session_id" INTEGER NOT NULL,'
        ' "user_id" INTEGER NOT NULL, "message" TEXT NOT NULL, "time" DATETIME NOT NULL, FOREIGN KEY ("session_id")'
        ' REFERENCES "multiplayer_session" ("id"), FOREIGN KEY ("user_id") REFERENCES "user" ("id"))',
        'CREATE INDEX "multiplayer_audit_entry_session_id" ON "multiplayer_audit_entry" ("session_id")',
        'CREATE INDEX "multiplayer_audit_entry_user_id" ON "multiplayer_audit_entry" ("user_id")',
        'CREATE TABLE "multiplayer_membership" ("user_id" INTEGER NOT NULL, "session_id" INTEGER NOT NULL,'
        ' "admin" INTEGER NOT NULL, "join_date" DATETIME NOT NULL, "can_help_layout_generation" INTEGER NOT NULL,'
        ' PRIMARY KEY ("user_id", "session_id"), FOREIGN KEY ("user_id") REFERENCES "user" ("id"),'
        ' FOREIGN KEY ("session_id") REFERENCES "multiplayer_session" ("id"))',
        'CREATE INDEX "multiplayer_membership_user_id" ON "multiplayer_membership" ("user_id")',
        'CREATE INDEX "multiplayer_membership_session_id" ON "multiplayer_membership" ("session_id")',
        'CREATE TABLE "performed_database_migrations" ("id" INTEGER NOT NULL PRIMARY KEY,'
        ' "migration" VARCHAR(255) NOT NULL)',
        'CREATE UNIQUE INDEX "performed_database_migrations_migration"'
        ' ON "performed_database_migrations" ("migration")',
        'CREATE TABLE "user_access_token" ("user_id" INTEGER NOT NULL, "name" VARCHAR(255) NOT NULL,'
        ' "creation_date" DATETIME NOT NULL, "last_used" DATETIME NOT NULL, PRIMARY KEY ("user_id", "name"),'
        ' FOREIGN KEY ("user_id") REFERENCES "user" ("id"))',
        'CREATE INDEX "user_access_token_user_id" ON "user_access_token" ("user_id")',
        'CREATE TABLE "world" ("id" INTEGER NOT NULL PRIMARY KEY, "session_id" INTEGER NOT NULL, "uuid" TEXT NOT NULL,'
        ' "name" VARCHAR(30) NOT NULL, "preset" TEXT NOT NULL, "order" INTEGER, FOREIGN KEY ("session_id")'
        ' REFERENCES "multiplayer_session" ("id"))',
        'CREATE INDEX "world_session_id" ON "world" ("session_id")',
        'CREATE UNIQUE INDEX "world_uuid" ON "world" ("uuid")',
        'CREATE TABLE "world_action" ("provider_id" INTEGER NOT NULL, "location" INTEGER NOT NULL,'
        ' "session_id" INTEGER NOT NULL, "receiver_id" INTEGER NOT NULL, "time" DATETIME NOT NULL,'
        ' PRIMARY KEY ("provider_id", "location"), FOREIGN KEY ("provider_id") REFERENCES "world" ("id"),'
        ' FOREIGN KEY ("session_id") REFERENCES "multiplayer_session" ("id"), FOREIGN KEY ("receiver_id")'
        ' REFERENCES "world" ("id"))',
        'CREATE INDEX "world_action_provider_id" ON "world_action" ("provider_id")',
        'CREATE INDEX "world_action_session_id" ON "world_action" ("session_id")',
        'CREATE INDEX "world_action_receiver_id" ON "world_action" ("receiver_id")',
        'CREATE TABLE "world_user_association" ("world_id" INTEGER NOT NULL, "user_id" INTEGER NOT NULL,'
        ' "connection_state" VARCHAR(255) NOT NULL, "last_activity" DATETIME NOT NULL, "inventory" BLOB,'
        ' PRIMARY KEY ("world_id", "user_id"), FOREIGN KEY ("world_id") REFERENCES "world" ("id"),'
        ' FOREIGN KEY ("user_id") REFERENCES "user" ("id"))',
        'CREATE INDEX "world_user_association_world_id" ON "world_user_association" ("world_id")',
        'CREATE INDEX "world_user_association_user_id" ON "world_user_association" ("user_id")',
        'INSERT INTO user VALUES (1, NULL, "you", 1)',
        'INSERT INTO multiplayer_session VALUES (1, "Session", NULL, "in-progress", NULL, NULL, 1,'
        ' "now", NULL, NULL, 0, 0)',
    ]:
        empty_database.execute_sql(sql)

    empty_database.create_tables([database.PerformedDatabaseMigrations])
    database_migration.apply_migrations()

    session = database.MultiplayerSession.get_by_id(1)
    assert session.create_session_entry() == multiplayer_session.MultiplayerSessionEntry(
        id=1,
        name="Session",
        worlds=[],
        users_list=[],
        game_details=None,
        visibility=MultiplayerSessionVisibility.VISIBLE,
        generation_in_progress=None,
        allowed_games=ANY,
        allow_coop=False,
        allow_everyone_claim_world=False,
    )
