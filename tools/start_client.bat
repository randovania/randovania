

cd /D "%~dp0"
cd ..

call venv\scripts\activate
set RANDOVANIA_SKIP_COMPILE=1

python setup.py build_ui
python -m randovania gui main
