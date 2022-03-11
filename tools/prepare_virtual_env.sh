#!/usr/bin/env bash

set -e -x
cd -- "$( dirname -- "${BASH_SOURCE[0]}" )/.."

python3.9 tools/test_py_version.py

python3.9 -m venv venv
source venv/bin/activate
python -c "import sys; assert sys.version_info[0:2] == (3, 9), 'Python 3.9 required'"
python -m pip install --upgrade -r requirements-setuptools.txt
python -m pip install -e ".[gui]" -c requirements.txt

echo "Setup finished successfully."
