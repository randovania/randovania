cd /D "%~dp0"
cd ..

call venv\scripts\activate
python -m randovania --configuration tools/dev-server-configuration.json gui --preview main
