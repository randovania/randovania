import base64

import flask

import randovania
from randovania.server import game_session, user_session, database
from randovania.server.server_app import ServerApp


def create_app():
    configuration = randovania.get_configuration()

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

    return app
