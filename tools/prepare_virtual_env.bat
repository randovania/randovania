@echo off
cd /D "%~dp0"
cd ..

if NOT exist .git\ (
    echo.
    echo Downloading Randovania via the "Download ZIP" button in GitHub is not supported.
    echo.
    echo Please follow the instructions in the README:
    echo   https://github.com/randovania/randovania/blob/main/README.md#installation
    echo.
    pause
    exit
)

py -3.12 tools\check_py_version.py
if NOT ["%errorlevel%"]==["0"] pause
if NOT ["%errorlevel%"]==["0"] exit /b 0

py -3.12 -m venv venv
if %errorlevel% neq 0 exit /b %errorlevel%

call venv\scripts\activate

python -c "import sys; assert sys.version_info[0:2] == (3, 12), 'Python 3.12 required'"
python -c "import sys; assert sys.maxsize > 2**32, '64-bit python required'"
if %errorlevel% neq 0 exit /b %errorlevel%

python -m pip install --upgrade -r requirements-setuptools.txt
python -m pip install pyqt-distutils pre-commit -e ".[gui]" -c requirements.txt
pre-commit install

echo Setup finished successfully.
pause
