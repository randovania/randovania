

cd /D "%~dp0"
cd ..

call venv\scripts\activate
python setup.py build_ui
python -m randovania gui --preview main
