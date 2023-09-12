import logging
import time
from logging.config import dictConfig
from pathlib import Path

import flask
import werkzeug.middleware.proxy_fix
from flask_socketio import ConnectionRefusedError

import randovania
import randovania.server.multiplayer.world_api
from randovania.server import client_check, database, multiplayer, user_session
from randovania.server.multiplayer import world_api
from randovania.server.server_app import ServerApp


class ServerLoggingFormatter(logging.Formatter):
    converter = time.gmtime

    def format(self, record):
        if flask.has_request_context():
            who = flask.request.remote_addr
            is_socketio = hasattr(flask.request, "sid")

            where = flask.request.url

            if is_socketio:
                record.context = "SocketIO"
                user = getattr(flask.request, "current_user", None)
                if user is not None:
                    who = user.name
                where = getattr(flask.request, "message", where)
            else:
                record.context = "Flask"

            record.who = who
            record.where = where

        else:
            record.who = None
            record.where = None
            record.context = "Free"

        return super().format(record)


def create_app():
    configuration = randovania.get_configuration()

    dictConfig(
        {
            "version": 1,
            "formatters": {
                "default": {
                    "format": "[%(asctime)s] %(context)s [%(who)s] %(levelname)s in %(where)s: %(message)s",
                    "class": "randovania.server.app.ServerLoggingFormatter",
                }
            },
            "handlers": {
                "wsgi": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://flask.logging.wsgi_errors_stream",
                    "formatter": "default",
                }
            },
            "loggers": {
                # Enable peewee logging to see the queries being made
                # 'peewee': {
                #     'level': 'DEBUG',
                # },
            },
            "root": {"level": "INFO", "handlers": ["wsgi"]},
        }
    )

    app = flask.Flask(__name__)
    app.wsgi_app = werkzeug.middleware.proxy_fix.ProxyFix(app.wsgi_app, x_proto=1, x_prefix=1)
    app.config["SECRET_KEY"] = configuration["server_config"]["secret_key"]
    app.config["GUEST_KEY"] = configuration["guest_secret"].encode("ascii") if "guest_secret" in configuration else None
    app.config["DISCORD_CLIENT_ID"] = configuration["discord_client_id"]
    app.config["DISCORD_CLIENT_SECRET"] = configuration["server_config"]["discord_client_secret"]
    app.config["DISCORD_REDIRECT_URI"] = f'{configuration["server_address"]}/login_callback'
    app.config["FERNET_KEY"] = configuration["server_config"]["fernet_key"].encode("ascii")
    app.config["ENFORCE_ROLE"] = configuration["server_config"].get("enforce_role")
    version_checking = client_check.ClientVersionCheck(configuration["server_config"]["client_version_checking"])

    db_existed = Path(configuration["server_config"]["database_path"]).exists()
    database.db.init(configuration["server_config"]["database_path"])
    database.db.connect(reuse_if_open=True)
    database.db.create_tables(database.all_classes)
    if not db_existed:
        for entry in database.DatabaseMigrations:
            database.PerformedDatabaseMigrations.create(migration=entry)

    from randovania.server import database_migration

    database_migration.apply_migrations()

    sa = ServerApp(app)
    app.sa = sa
    multiplayer.setup_app(sa)
    user_session.setup_app(sa)

    connected_clients = sa.metrics.info("connected_clients", "How many clients are connected right now.")
    connected_clients.set(0)

    @app.route("/")
    def index():
        app.logger.info(
            "Version checked by %s (%s)",
            flask.request.environ["REMOTE_ADDR"],
            flask.request.environ.get("HTTP_X_FORWARDED_FOR"),
        )
        return randovania.VERSION

    server_version = randovania.VERSION

    @sa.get_server().on("connect")
    def connect(sid, environ):
        try:
            if "HTTP_X_RANDOVANIA_VERSION" not in environ:
                raise ConnectionRefusedError("unknown client version")

            client_app_version = environ["HTTP_X_RANDOVANIA_VERSION"]
            error_message = client_check.check_client_version(version_checking, client_app_version, server_version)
            if error_message is None and not randovania.is_dev_version():
                error_message = client_check.check_client_headers(sa.expected_headers, environ)

            forwarded_for = environ.get("HTTP_X_FORWARDED_FOR")

            if error_message is not None:
                app.logger.info(
                    f"Client {sid} at {environ['REMOTE_ADDR']} ({forwarded_for}) with "
                    f"version {client_app_version} tried to connect, but refused with {error_message}."
                )
                raise ConnectionRefusedError(error_message)

            connected_clients.inc()

            app.logger.info(
                f"Client {sid} at {environ['REMOTE_ADDR']} ({forwarded_for}) with "
                f"version {client_app_version} connected."
            )

        except ConnectionRefusedError:
            # Do not wrap if it's already a ConnectionRefusedError
            raise

        except Exception as e:
            logging.exception(f"Unknown exception when testing the client's headers: {e}")
            raise ConnectionRefusedError(f"Unable to check if request is valid: {e}.\nPlease file a bug report.")

    @sa.get_server().on("disconnect")
    def disconnect(sid):
        connected_clients.dec()

        app.logger.info(f"Client at {sa.current_client_ip(sid)} disconnected.")

        session = sa.get_server().get_session(sid)
        world_api.report_disconnect(sa, session, app.logger)

    return app
