python -m venv venv-requirements
call venv-requirements\Scripts\activate
python -m pip install --use-feature=2020-resolver -r requirements-setuptools.txt
python -m pip install --use-feature=2020-resolver -e . -e ".[gui]" -e ".[server]" -e ".[test]" "PyInstaller" "pyqt-distutils"
python -m pip freeze > requirements.txt