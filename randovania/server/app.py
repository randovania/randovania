import logging
import time
from logging.config import dictConfig

import flask
import werkzeug.middleware.proxy_fix
from flask_socketio import ConnectionRefusedError

import randovania
from randovania.server import game_session, user_session, database, client_check
from randovania.server.server_app import ServerApp


def create_app():
    configuration = randovania.get_configuration()

    logging.Formatter.converter = time.gmtime
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
    app.config["ENFORCE_ROLE"] = configuration["server_config"].get("enforce_role")
    version_checking = client_check.ClientVersionCheck(configuration["server_config"]["client_version_checking"])

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
        return randovania.VERSION

    server_version = randovania.VERSION

    @sio.sio.server.on("connect")
    def connect(sid, environ):
        try:
            if "HTTP_X_RANDOVANIA_VERSION" not in environ:
                raise ConnectionRefusedError("unknown client version")

            client_app_version = environ["HTTP_X_RANDOVANIA_VERSION"]
            error_message = client_check.check_client_version(version_checking, client_app_version, server_version)
            if error_message is None and not randovania.is_dev_version():
                error_message = client_check.check_client_headers(sio.expected_headers, environ)

            if error_message is not None:
                raise ConnectionRefusedError(error_message)

            connected_clients.inc()

            forwarded_for = environ.get('HTTP_X_FORWARDED_FOR')
            app.logger.info(f"Client {sid} at {environ['REMOTE_ADDR']} ({forwarded_for}) with "
                            f"version {client_app_version} connected.")

        except ConnectionRefusedError:
            # Do not wrap if it's already a ConnectionRefusedError
            raise

        except Exception as e:
            logging.exception(f"Unknown exception when testing the client's headers: {e}")
            raise ConnectionRefusedError(f"Unable to check if request is valid: {e}.\n"
                                         f"Please file a bug report.")

    @sio.sio.server.on("disconnect")
    def disconnect(sid):
        connected_clients.dec()

        app.logger.info(f"Client at {sio.current_client_ip(sid)} disconnected.")

        session = sio.get_server().get_session(sid)
        if "user-id" in session:
            game_session.report_user_disconnected(sio, session["user-id"], app.logger)

    return app
