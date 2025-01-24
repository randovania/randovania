#!/usr/bin/env bash

set -e -x
cd -- "$( dirname -- "${BASH_SOURCE[0]}" )/.."

if [ ! -d "./.git" ]; then
    echo ""
    echo "Downloading Randovania via the \"Download ZIP\" button in GitHub is not supported."
    echo ""
    echo "Please follow the instructions in the README:"
    echo "  https://github.com/randovania/randovania/blob/main/README.md#installation"
    echo ""
    read -p "Press enter to exit."
    exit
fi

python3.12 tools/check_py_version.py

python3.12 -m venv venv
source venv/bin/activate
python -c "import sys; assert sys.version_info[0:2] == (3, 12), 'Python 3.12 required'"
python -m pip install --upgrade -r requirements-setuptools.txt
python -m pip install pyqt-distutils pre-commit -e ".[gui]" -c requirements.txt
pre-commit install

echo "Setup finished successfully."
