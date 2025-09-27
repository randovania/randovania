# uvicorn reload/workers require importing from a module rather than
# using a factory or instance. don't import this unless you're actually
# running the server

import randovania
from randovania.server.server_app import ServerApp

server_app = ServerApp(randovania.get_configuration())
app = server_app.app
