

cd /D "%~dp0"
cd ..

py -3.10 -m venv venv
call venv\scripts\activate
python -m pip install --upgrade -r requirements-setuptools.txt
python -m pip install --upgrade -r requirements-small.txt
python -m pip install -e . -e ".[gui]"

echo Setup finished successfully.
pause
