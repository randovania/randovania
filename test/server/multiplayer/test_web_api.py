from unittest.mock import MagicMock

from randovania.server.multiplayer import web_api


def test_admin_sessions(server_app, solo_two_world_session):
    # Setup
    web_api.setup_app(server_app)

    # Run
    with server_app.app.test_request_context("/sessions"):
        result = web_api.admin_sessions(MagicMock())

    entry = (
        "<td>The Name</td>"
        '<td>2020-05-02 10:20:00+00:00</td><td>In-Progress</td><td>1</td><td>2</td></tr>'
    )
    assert entry in result


def test_admin_session(server_app, solo_two_world_session):
    # Setup
    web_api.setup_app(server_app)

    # Run
    with server_app.app.test_request_context("/session/1"):
        result = web_api.admin_session(MagicMock(), 1)

    entry = (
        '<td>The Name</td><td>World 1</td><td>Disconnected</td><td>Missing</td>'
    )
    assert entry in result
