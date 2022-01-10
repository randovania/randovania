@echo off
cd /D "%~dp0"
cd ..

python3 tools\test_py_version.py
if NOT ["%errorlevel%"]==["0"] pause
if NOT ["%errorlevel%"]==["0"] exit /b 0

py -3.9 -m venv venv
call venv\scripts\activate
python -m pip install --upgrade -r requirements-setuptools.txt
python -m pip install --upgrade -r requirements-small.txt
python -m pip install -e . -e ".[gui]"

echo Setup finished successfully.
pause
