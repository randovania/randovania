#!/usr/bin/env bash

set -e -x
cd -- "$( dirname -- "${BASH_SOURCE[0]}" )/.."

python3.11 tools/test_py_version.py

python3.11 -m venv venv
source venv/bin/activate
python -c "import sys; assert sys.version_info[0:2] == (3, 11), 'Python 3.11 required'"
python -m pip install --upgrade -r requirements-setuptools.txt
python -m pip install pyqt-distutils -e ".[gui]" -c requirements.txt

echo "Setup finished successfully."
