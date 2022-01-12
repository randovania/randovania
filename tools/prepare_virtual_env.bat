@echo off
cd /D "%~dp0"
cd ..

py -3.9 tools\test_py_version.py
if NOT ["%errorlevel%"]==["0"] pause
if NOT ["%errorlevel%"]==["0"] exit /b 0

py -3.9 -m venv venv
if %errorlevel% neq 0 exit /b %errorlevel%

call venv\scripts\activate

python -c "import sys; assert sys.version_info[0:2] == (3, 9), 'Python 3.9 required'"
python -c "import sys; assert sys.maxsize > 2**32, '64-bit python required'"
if %errorlevel% neq 0 exit /b %errorlevel%

python -m pip install --upgrade -r requirements-setuptools.txt
python -m pip install --upgrade -r requirements-small.txt
python -m pip install -e . -e ".[gui]"

echo Setup finished successfully.
pause
