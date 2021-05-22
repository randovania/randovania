from argparse import ArgumentParser


def flask_command_logic(args):
    from randovania.server import app
    server_app = app.create_app()
    server_app.sio.sio.run(server_app, host="0.0.0.0")


def add_flask_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "flask",
        help="Hosts the flask server."
    )
    parser.set_defaults(func=flask_command_logic)


def migrate_database_command_logic(args):
    from randovania.server import database_migration
    database_migration.apply_migrations()


def add_migrate_database_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "migrate-database",
        help="Apply schema migrations to the database."
    )
    parser.set_defaults(func=migrate_database_command_logic)


def bot_command_logic(args):
    from randovania.server import bot
    bot.run()


def add_bot_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "bot",
        help="Runs the Discord bot."
    )
    parser.set_defaults(func=bot_command_logic)


def create_subparsers(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "server",
        help="CLI tools for the server tools"
    )
    sub_parsers = parser.add_subparsers(dest="command")
    add_flask_command(sub_parsers)
    add_migrate_database_command(sub_parsers)
    add_bot_command(sub_parsers)

    def check_command(args):
        if args.command is None:
            parser.print_help()
            raise SystemExit(1)

    parser.set_defaults(func=check_command)
