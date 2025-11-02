from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace, _SubParsersAction


def run_command_logic(args: Namespace) -> None:
    import randovania

    sampling_rate = randovania.get_configuration().get("sentry_sampling_rate", 1.0)

    import randovania.monitoring

    randovania.monitoring.server_init(sampling_rate=sampling_rate)

    host = "0.0.0.0"
    reload_ = False

    if args.mode == "dev":
        reload_ = True
        os.environ["FASTAPI_DEBUG"] = "True"
    elif args.mode != "prod":
        logging.warning(f"Unknown server mode '{args.mode}'. Running in prod mode.")

    import uvicorn
    import uvicorn.config

    log_config = uvicorn.config.LOGGING_CONFIG

    # # Enable peewee logging to see the queries being made
    # log_config["loggers"]["peewee"] = {
    #     'level': 'DEBUG',
    #     'handlers': ['default'],
    # }

    # the info-level logs are more like debug-level
    log_config["loggers"]["socketio_handler.app"] = {"level": "WARN"}
    log_config["loggers"]["watchfiles.main"] = {"level": "WARN"}

    log_config["formatters"]["default"]["fmt"] = (
        "[%(asctime)s] %(levelprefix)s %(context)s [%(who)s] in %(where)s: %(message)s"
    )
    log_config["formatters"]["default"]["()"] = "randovania.server.server_app.ServerLoggingFormatter"
    log_config["formatters"]["access"]["fmt"] = (
        "[%(asctime)s] %(levelprefix)s Uvicorn [%(client_addr)s] in %(request_line)s: %(status_code)s"
    )

    uvicorn.run(
        "randovania.server.app_module:app",
        host=host,
        port=5000,
        log_config=log_config,
        reload=reload_,
        reload_excludes=[
            "randovania/version_hash.py",
            "randovania/version.py",
            ".venv/Lib/site-packages/__editable___randovania_*_finder.py",
        ],
        forwarded_allow_ips="*",
    )


def add_run_command(sub_parsers: _SubParsersAction) -> None:
    parser: ArgumentParser = sub_parsers.add_parser("run", help="Hosts the FastAPI server.")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["dev", "prod"],
        default="prod",
        help="Whether to run in development or production mode.",
    )
    parser.set_defaults(func=run_command_logic)


def migrate_database_command_logic(args: Namespace) -> None:
    from randovania.server import database_migration

    database_migration.apply_migrations()


def add_migrate_database_command(sub_parsers: _SubParsersAction) -> None:
    parser: ArgumentParser = sub_parsers.add_parser("migrate-database", help="Apply schema migrations to the database.")
    parser.set_defaults(func=migrate_database_command_logic)


def bot_command_logic(args: Namespace) -> None:
    import randovania.monitoring

    randovania.monitoring.bot_init()

    from randovania.discord_bot import bot

    bot.run()


def add_bot_command(sub_parsers: _SubParsersAction) -> None:
    parser: ArgumentParser = sub_parsers.add_parser("bot", help="Runs the Discord bot.")
    parser.set_defaults(func=bot_command_logic)


def create_subparsers(sub_parsers: _SubParsersAction) -> None:
    parser: ArgumentParser = sub_parsers.add_parser("server", help="CLI tools for the server tools")
    sub_parsers = parser.add_subparsers(dest="command")
    add_run_command(sub_parsers)
    add_migrate_database_command(sub_parsers)
    add_bot_command(sub_parsers)

    def check_command(args: Namespace) -> None:
        if args.command is None:
            parser.print_help()
            raise SystemExit(1)

    parser.set_defaults(func=check_command)
