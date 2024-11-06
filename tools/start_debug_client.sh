#!/usr/bin/env bash

set -e -x
cd -- "$( dirname -- "${BASH_SOURCE[0]}" )/.."

source venv/bin/activate
python -m randovania --configuration tools/dev-server-configuration.json gui --preview main
