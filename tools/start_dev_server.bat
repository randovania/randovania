cd /D "%~dp0"
cd ..

set FLASK_DEBUG=1
python -m randovania --configuration tools/dev-server-configuration.json server flask --mode dev
