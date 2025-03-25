@echo off
cd /D "%~dp0"
cd ..

>nul 2>nul where uv
IF %ERRORLEVEL% NEQ 0 powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

uv run tools/prepare_virtual_env.py %*
pause
