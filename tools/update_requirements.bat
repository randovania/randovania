python -m venv venv-requirements
call venv-requirements\Scripts\activate
python -m pip install -r requirements-setuptools.txt
python -m pip install -e . -e ".[gui]" -e ".[server]" -e ".[test]" "PyInstaller" "pyqt-distutils"
python -m pip freeze > requirements.txt
