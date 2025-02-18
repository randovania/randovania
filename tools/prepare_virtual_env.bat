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

if [%1]!=["--all"] goto thin
uv sync --frozen --all-extras
goto final

:thin
uv sync --frozen --extra gui

:final
uvx pre-commit install

echo Setup finished successfully.
pause
