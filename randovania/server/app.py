from logging.config import dictConfig

import flask
from flask_socketio import ConnectionRefusedError

import randovania
from randovania.interface_common.update_checker import strict_version_for_version_string, strict_current_version
from randovania.server import game_session, user_session, database
from randovania.server.server_app import ServerApp


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
    app.config['SECRET_KEY'] = configuration["server_config"]["secret_key"]
    app.config["GUEST_KEY"] = configuration["guest_secret"].encode("ascii") if "guest_secret" in configuration else None
    app.config["DISCORD_CLIENT_ID"] = configuration["discord_client_id"]
    app.config["DISCORD_CLIENT_SECRET"] = configuration["server_config"]["discord_client_secret"]
    app.config["DISCORD_REDIRECT_URI"] = "http://127.0.0.1:5000/callback/"  # Redirect URI.
    app.config["FERNET_KEY"] = configuration["server_config"]["fernet_key"].encode("ascii")

    database.db.init(configuration["server_config"]['database_path'])
    database.db.connect(reuse_if_open=True)
    database.db.create_tables(database.all_classes)

    sio = ServerApp(app)
    app.sio = sio
    game_session.setup_app(sio)
    user_session.setup_app(sio)

    @app.route("/")
    def index():
        return "ok"

    server_version = strict_current_version()

    @sio.sio.server.on("connect")
    def connect(sid, environ):
        if "HTTP_X_RANDOVANIA_VERSION" not in environ:
            raise ConnectionRefusedError("unknown client version")

        try:
            client_app_version = strict_version_for_version_string(environ["HTTP_X_RANDOVANIA_VERSION"])
        except ValueError:
            raise ConnectionRefusedError("unknown client version")

        app.logger.info(f"Client at {environ['REMOTE_ADDR']} with "
                        f"version {client_app_version} connected, while server is {server_version}")

    return app
