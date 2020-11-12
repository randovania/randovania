from logging.config import dictConfig

import flask
from flask_socketio import ConnectionRefusedError

import randovania
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
    app.config["STRICT_CLIENT_VERSION"] = configuration["server_config"]["strict_client_version"]

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

    @sio.sio.server.on("connect")
    def connect(sid, environ):
        if "HTTP_X_RANDOVANIA_VERSION" not in environ:
            raise ConnectionRefusedError("unknown client version")

        client_app_version = environ["HTTP_X_RANDOVANIA_VERSION"]
        if app.config["STRICT_CLIENT_VERSION"] and server_version != client_app_version:
            raise ConnectionRefusedError(f"Incompatible client version '{client_app_version}', "
                                         f"expected '{server_version}'")

        connected_clients.inc()

        forwarded_for = environ.get('HTTP_X_FORWARDED_FOR')
        app.logger.info(f"Client at {environ['REMOTE_ADDR']} ({forwarded_for}) with "
                        f"version {client_app_version} connected.")

    @sio.sio.server.on("disconnect")
    def disconnect(sid):
        connected_clients.dec()
        sio_environ = sio.get_server().environ

        forwarded_for = sio_environ.get('HTTP_X_FORWARDED_FOR')
        app.logger.info(f"Client at {sio_environ[sid]['REMOTE_ADDR']} ({forwarded_for}) disconnected.")

        session = sio.get_server().get_session(sid)
        if "user-id" in session:
            game_session.report_user_disconnected(sio, session["user-id"], app.logger)

    return app
