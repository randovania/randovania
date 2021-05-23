def apply_migrations():
    import playhouse.migrate
    import randovania
    from randovania.server import database

    randovania.setup_logging('DEBUG', None)

    configuration = randovania.get_configuration()
    database.db.init(configuration["server_config"]['database_path'])
    database.db.connect(reuse_if_open=True)
    migrator = playhouse.migrate.SqliteMigrator(database.db)

    with database.db.atomic():
        playhouse.migrate.migrate(
            migrator.rename_table("gamesession", "game_session"),
            migrator.rename_table("gamesessionmembership", "game_session_membership"),
            migrator.rename_table("gamesessionpreset", "game_session_preset"),
            migrator.rename_table("gamesessionteamaction", "game_session_team_action"),
            migrator.add_column("game_session", "dev_features", database.GameSession.dev_features),
        )
