from distutils.version import StrictVersion
from enum import Enum
from logging.config import dictConfig

import flask
import werkzeug.middleware.proxy_fix
from flask_socketio import ConnectionRefusedError

import randovania
from randovania.network_common import connection_headers
from randovania.server import game_session, user_session, database
from randovania.server.server_app import ServerApp


class ClientVersionCheck(Enum):
    STRICT = "strict"
    MATCH_MAJOR_MINOR = "match-major-minor"
    IGNORE = "ignore"


def check_client_version(version_checking: ClientVersionCheck, client_version: str, server_version: str):
    if version_checking == ClientVersionCheck.STRICT:
        if server_version != client_version:
            raise ConnectionRefusedError(f"Incompatible client version '{client_version}', "
                                         f"expected '{server_version}'")
    elif version_checking == ClientVersionCheck.MATCH_MAJOR_MINOR:
        server = StrictVersion(server_version.split(".dev")[0])
        client = StrictVersion(client_version.split(".dev")[0])
        if server.version[:2] != client.version[:2]:
            shorter_client = "{}.{}".format(*client.version[:2])
            shorter_server = "{}.{}".format(*server.version[:2])
            raise ConnectionRefusedError(f"Incompatible client version '{shorter_client}', "
                                         f"expected '{shorter_server}'")


def create_app():
    configuration = randovania.get_configuration()

    dictConfig({
        'version': 1,
        'formatters': {'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }},
        'handlers': {'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        }},
        'root': {
            'level': 'INFO',
            'handlers': ['wsgi']
        }
    })

    app = flask.Flask(__name__)
    app.wsgi_app = werkzeug.middleware.proxy_fix.ProxyFix(app.wsgi_app, x_proto=1, x_prefix=1)
    app.config['SECRET_KEY'] = configuration["server_config"]["secret_key"]
    app.config["GUEST_KEY"] = configuration["guest_secret"].encode("ascii") if "guest_secret" in configuration else None
    app.config["DISCORD_CLIENT_ID"] = configuration["discord_client_id"]
    app.config["DISCORD_CLIENT_SECRET"] = configuration["server_config"]["discord_client_secret"]
    app.config["DISCORD_REDIRECT_URI"] = f'{configuration["server_address"]}/login_callback'
    app.config["FERNET_KEY"] = configuration["server_config"]["fernet_key"].encode("ascii")
    version_checking = ClientVersionCheck(configuration["server_config"]["client_version_checking"])

    database.db.init(configuration["server_config"]['database_path'])
    database.db.connect(reuse_if_open=True)
    database.db.create_tables(database.all_classes)

    sio = ServerApp(app)
    app.sio = sio
    game_session.setup_app(sio)
    user_session.setup_app(sio)

    connected_clients = sio.metrics.info("connected_clients", "How many clients are connected right now.")
    connected_clients.set(0)

    @app.route("/")
    def index():
        return "ok"

    server_version = randovania.VERSION
    expected_headers = connection_headers()
    expected_headers.pop("X-Randovania-Version")

    @sio.sio.server.on("connect")
    def connect(sid, environ):
        if "HTTP_X_RANDOVANIA_VERSION" not in environ:
            raise ConnectionRefusedError("unknown client version")

        client_app_version = environ["HTTP_X_RANDOVANIA_VERSION"]
        check_client_version(version_checking, client_app_version, server_version)

        wrong_headers = {}
        for name, expected in expected_headers.items():
            value = environ.get("HTTP_{}".format(name.upper().replace("-", "_")))
            if value != expected:
                wrong_headers[name] = value

        if wrong_headers:
            raise ConnectionRefusedError("\n".join(
                f"Expected '{expected_headers[name]}' for '{name}', got '{value}'"
                for name, value in wrong_headers.values()
            ))

        connected_clients.inc()

        forwarded_for = environ.get('HTTP_X_FORWARDED_FOR')
        app.logger.info(f"Client at {environ['REMOTE_ADDR']} ({forwarded_for}) with "
                        f"version {client_app_version} connected.")

    @sio.sio.server.on("disconnect")
    def disconnect(sid):
        connected_clients.dec()
        sio_environ = sio.get_server().environ

        forwarded_for = sio_environ[sid].get('HTTP_X_FORWARDED_FOR')
        app.logger.info(f"Client at {sio_environ[sid]['REMOTE_ADDR']} ({forwarded_for}) disconnected.")

        session = sio.get_server().get_session(sid)
        if "user-id" in session:
            game_session.report_user_disconnected(sio, session["user-id"], app.logger)

    return app
