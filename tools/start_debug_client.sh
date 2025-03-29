#!/usr/bin/env bash

set -e -x
cd -- "$( dirname -- "${BASH_SOURCE[0]}" )/.."

uv run randovania --configuration tools/dev-server-configuration.json gui --preview main
