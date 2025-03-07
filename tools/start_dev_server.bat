cd /D "%~dp0"
cd ..

set FLASK_DEBUG=1
uv run randovania --configuration tools/dev-server-configuration.json server flask
