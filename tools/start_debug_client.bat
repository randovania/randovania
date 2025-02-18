cd /D "%~dp0"
cd ..

uv run randovania --configuration tools/dev-server-configuration.json gui --preview main
