import flask

import randovania
from randovania.server import game_session, user_session
from randovania.server.socket_wrapper import SocketWrapper


def create_app():
    app = flask.Flask(__name__)
    app.config['SECRET_KEY'] = 'secret!'

    configuration = randovania.get_configuration()
    app.config["DISCORD_CLIENT_ID"] = configuration["discord_client_id"]
    app.config["DISCORD_CLIENT_SECRET"] = configuration["discord_client_secret"]
    app.config["DISCORD_REDIRECT_URI"] = "http://127.0.0.1:5000/callback/"  # Redirect URI.

    sio = SocketWrapper(app)
    app.sio = sio
    game_session.setup_app(sio)
    user_session.setup_app(app, sio)

    @app.route("/")
    def index():
        return "ok"

    return app
