from randovania.server.multiplayer import session_admin, session_api, web_api, world_api
from randovania.server.server_app import ServerApp


def setup_app(sa: ServerApp):
    session_api.setup_app(sa)
    session_admin.setup_app(sa)
    web_api.setup_app(sa)
    world_api.setup_app(sa)
