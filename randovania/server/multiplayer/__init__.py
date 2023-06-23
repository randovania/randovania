from randovania.server.multiplayer import session_api, session_admin, web_api, world_api
from randovania.server.server_app import ServerApp


def setup_app(sio: ServerApp):
    session_api.setup_app(sio)
    session_admin.setup_app(sio)
    web_api.setup_app(sio)
    world_api.setup_app(sio)
